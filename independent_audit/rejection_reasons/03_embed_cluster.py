"""Step 3: local embeddings + UMAP + HDBSCAN on the de-identified substantive reason segments of rejections (seeded).

Same method as delay_reasons/03 (its `embed` and `ctfidf` functions are imported read-only):
  embedder intfloat/multilingual-e5-small (local, sentence-transformers; fallback TF-IDF char 3-5 grams + SVD128 if unavailable);
  UMAP(10 dims, cosine, n_neighbors=15, min_dist=0, random_state=42);
  HDBSCAN(min_cluster_size=12, min_samples=4) -- smaller than for postponements (2.2k vs 5.9k segments);
  noise attached to the nearest centroid if cosine >= 10th percentile of member similarities;
  cross-check k-means on the UMAP space, k by silhouette over 8..30, ARI vs HDBSCAN.
Outputs: _tmp/seg_clusters.pkl, _tmp/embeddings.npy, _tmp/cluster_inspection.txt (de-identified; deleted at the end), 03_*.out.txt.
"""
import sys; sys.dont_write_bytecode = True  # never leave __pycache__ in delay_reasons (read-only reuse)
import os, json, importlib.util
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__)); TMP = os.path.join(HERE, '_tmp')
SEED = 42
np.random.seed(SEED)
spec = importlib.util.spec_from_file_location('dr03', os.path.join(HERE, '..', 'delay_reasons', '03_embed_cluster.py'))
DR03 = importlib.util.module_from_spec(spec); spec.loader.exec_module(DR03)


def main():
    S = pd.read_pickle(os.path.join(TMP, 'segments.pkl'))
    fp = os.path.join(TMP, 'embeddings.npy')
    if os.path.exists(fp) and len(np.load(fp)) == len(S):
        X = np.load(fp); emb_name = open(os.path.join(TMP, 'embedder.txt')).read()
    else:
        X, emb_name = DR03.embed(S.text.tolist()); np.save(fp, X); open(os.path.join(TMP, 'embedder.txt'), 'w').write(emb_name)
    import umap
    from sklearn.cluster import HDBSCAN, KMeans
    from sklearn.metrics import silhouette_score, adjusted_rand_score
    U = umap.UMAP(n_components=10, n_neighbors=15, min_dist=0.0, metric='cosine', random_state=SEED).fit_transform(X)
    np.save(os.path.join(TMP, 'umap.npy'), U)
    lab = HDBSCAN(min_cluster_size=12, min_samples=4).fit_predict(U)
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
    sil = {}
    for k in range(8, 31):
        km = KMeans(k, n_init=10, random_state=SEED).fit(U)
        sil[k] = float(silhouette_score(U, km.labels_, sample_size=min(4000, len(U)), random_state=SEED))
    kbest = max(sil, key=sil.get)
    kml = KMeans(kbest, n_init=10, random_state=SEED).fit_predict(U)
    m = lab2 != -1
    ari = float(adjusted_rand_score(lab2[m], kml[m]))
    S['cluster'] = lab2; S['cluster_raw'] = lab; S['kmeans'] = kml
    S.to_pickle(os.path.join(TMP, 'seg_clusters.pkl'))
    terms = DR03.ctfidf(S[S.cluster != -1], S.cluster[S.cluster != -1])
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
    out = dict(embedder=emb_name, segments=len(S), clusters=len(cl), noise_raw=round(noise0, 3),
               noise_after_attach=round(float((lab2 == -1).mean()), 3), attach_threshold=round(thr, 3),
               kmeans_best_k=kbest, silhouette_best=round(sil[kbest], 3), ari_hdbscan_kmeans=round(ari, 3))
    open(os.path.join(HERE, '03_embed_cluster.out.txt'), 'w', encoding='utf-8').write(json.dumps(out) + '\n')
    print(json.dumps(out, indent=1))


if __name__ == '__main__':
    main()
