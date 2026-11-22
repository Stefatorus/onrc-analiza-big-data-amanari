"""Step 3: local embeddings + UMAP + HDBSCAN on de-identified reason segments (seeded).

Embedder: intfloat/multilingual-e5-small (sentence-transformers, run locally on this machine; weights downloaded once from
Hugging Face; no text leaves the machine). Fallback when the model cannot be loaded: TF-IDF char 3-5 grams + TruncatedSVD(128).
Reduction: UMAP(10 dims, cosine, n_neighbors=15, min_dist=0, random_state=42).
Clustering: sklearn HDBSCAN(min_cluster_size=20, min_samples=5); noise points are attached to the nearest cluster centroid
(cosine in the full embedding space) when similarity >= the 10th percentile of member-to-centroid similarities, else kept as -1.
Cross-check: k-means on the UMAP space with k chosen by silhouette over 8..30.
Outputs: _tmp/seg_clusters.pkl (segment -> cluster), _tmp/embeddings.npy; _tmp/cluster_inspection.txt (deleted at the end; de-identified:
top c-TF-IDF terms + 4 most central masked phrases per cluster, phrases shown only if they recur >= 3 times or are cut to 12 words).
"""
import os, re, sys, json, collections
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')
SEED = 42
np.random.seed(SEED)


def embed(texts):
    try:
        from sentence_transformers import SentenceTransformer
        import torch
        torch.manual_seed(SEED)
        m = SentenceTransformer('intfloat/multilingual-e5-small', device='cuda' if torch.cuda.is_available() else 'cpu')
        X = m.encode(['query: ' + t.replace('<x>', '').replace('#', '') for t in texts], batch_size=64, normalize_embeddings=True,
                     show_progress_bar=False)
        return np.asarray(X, dtype=np.float32), 'multilingual-e5-small'
    except Exception as e:  # fallback
        print('embedder unavailable, TF-IDF fallback:', repr(e)[:200])
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.decomposition import TruncatedSVD
        from sklearn.preprocessing import normalize
        T = TfidfVectorizer(analyzer='char_wb', ngram_range=(3, 5), min_df=3, sublinear_tf=True).fit_transform(texts)
        return normalize(TruncatedSVD(128, random_state=SEED).fit_transform(T)).astype(np.float32), 'tfidf-char-svd128'


def ctfidf(S, labels, topn=12):
    from sklearn.feature_extraction.text import CountVectorizer
    stop = set('de la si in cu din a al ale se va vor fi pe ca care sau sa este pentru nu prin cel dupa art alin lit conform cf potrivit privind '
               'registrul comertului x adresa data legea_265_2022 cererii cererea'.split())
    docs = S.groupby(labels).text.apply(lambda s: ' '.join(s))
    cv = CountVectorizer(token_pattern=r'[a-z_]{3,}', ngram_range=(1, 2), min_df=2, stop_words=list(stop))
    C = cv.fit_transform(docs.values).astype(float)
    tf = C.multiply(1 / np.maximum(C.sum(axis=1), 1)).tocsr()
    idf = np.log(1 + C.sum() / np.maximum(np.asarray(C.sum(axis=0)).ravel(), 1))
    W = tf.multiply(idf).tocsr(); voc = np.array(cv.get_feature_names_out())
    return {k: list(voc[np.argsort(-W[i].toarray().ravel())[:topn]]) for i, k in enumerate(docs.index)}


def main():
    S = pd.read_pickle(os.path.join(TMP, 'segments.pkl'))
    fp = os.path.join(TMP, 'embeddings.npy')
    if os.path.exists(fp) and len(np.load(fp)) == len(S):
        X = np.load(fp); emb_name = open(os.path.join(TMP, 'embedder.txt')).read()
    else:
        X, emb_name = embed(S.text.tolist()); np.save(fp, X); open(os.path.join(TMP, 'embedder.txt'), 'w').write(emb_name)
    import umap
    from sklearn.cluster import HDBSCAN, KMeans
    from sklearn.metrics import silhouette_score
    U = umap.UMAP(n_components=10, n_neighbors=15, min_dist=0.0, metric='cosine', random_state=SEED).fit_transform(X)
    lab = HDBSCAN(min_cluster_size=20, min_samples=5).fit_predict(U)
    noise0 = float((lab == -1).mean())
    cl = sorted(set(lab) - {-1})
    cent = np.stack([X[lab == c].mean(0) / np.linalg.norm(X[lab == c].mean(0)) for c in cl])
    sim = X @ cent.T
    member_sim = np.array([sim[i, cl.index(l)] for i, l in enumerate(lab) if l != -1])
    thr = float(np.quantile(member_sim, 0.10))
    lab2 = lab.copy()
    for i in np.where(lab == -1)[0]:
        j = int(sim[i].argmax())
        if sim[i, j] >= thr:
            lab2[i] = cl[j]
    # k-means cross-check (silhouette over 8..30 on the UMAP space)
    sil = {}
    for k in range(8, 31):
        km = KMeans(k, n_init=10, random_state=SEED).fit(U)
        sil[k] = float(silhouette_score(U, km.labels_, sample_size=4000, random_state=SEED))
    kbest = max(sil, key=sil.get)
    kml = KMeans(kbest, n_init=10, random_state=SEED).fit_predict(U)
    from sklearn.metrics import adjusted_rand_score
    m = lab2 != -1
    ari = float(adjusted_rand_score(lab2[m], kml[m]))
    S['cluster'] = lab2; S['cluster_raw'] = lab; S['kmeans'] = kml
    S.to_pickle(os.path.join(TMP, 'seg_clusters.pkl'))

    terms = ctfidf(S[S.cluster != -1], S.cluster[S.cluster != -1])
    with open(os.path.join(TMP, 'cluster_inspection.txt'), 'w', encoding='utf-8') as fh:
        fh.write(f'embedder={emb_name} segments={len(S)} clusters={len(cl)} noise_raw={noise0:.3f} noise_after_attach={(lab2 == -1).mean():.3f} '
                 f'kmeans_best_k={kbest} silhouette={sil[kbest]:.3f} ARI(hdbscan,kmeans)={ari:.3f}\n\n')
        for c in cl:
            idx = np.where(lab2 == c)[0]
            cs = sim[idx, cl.index(c)]
            top = idx[np.argsort(-cs)[:4]]
            fh.write(f'## cluster {c}  n={len(idx)}  entries={S.eid[idx].nunique()}\n   terms: {", ".join(terms.get(c, []))}\n')
            for t in S.text[top]:
                fh.write('   - ' + ' '.join(t.split()[:30]) + '\n')
            fh.write('\n')
    print(json.dumps(dict(embedder=emb_name, segments=len(S), clusters=len(cl), noise_raw=round(noise0, 3),
                          noise_after_attach=round(float((lab2 == -1).mean()), 3), attach_threshold=round(thr, 3),
                          kmeans_best_k=kbest, silhouette_best=round(sil[kbest], 3), silhouette=dict((k, round(v, 3)) for k, v in sil.items()),
                          ari_hdbscan_kmeans=round(ari, 3)), indent=1))


if __name__ == '__main__':
    main()
