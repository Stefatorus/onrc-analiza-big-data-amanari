"""Build every volume in order: main report + executive edition, then volumes 0, 2, 3, 4, 5, 6, then lint all prose."""
import subprocess, sys
PY = sys.executable
steps = [[PY, "-X", "utf8", "build_raport_institutii.py"], [PY, "-X", "utf8", "build_raport_institutii.py", "--exec"],
         [PY, "-X", "utf8", "build_volume_stat.py", "--vol0", "--vol2", "--vol3", "--vol4", "--vol5", "--vol6"]]
for s in steps:
    r = subprocess.run(s); assert r.returncode == 0, s
for h in ["Raport_ONRC_Coada_2026-11.html", "Raport_ONRC_Coada_2026-11_EXECUTIV.html", "Raport_ONRC_Coada_2026-11_VOL0_Fise_pe_profil.html",
          "Raport_ONRC_Coada_2026-11_VOL3_Raport_statistic_avansat.html", "Raport_ONRC_Coada_2026-11_VOL4_Munca_din_spatele_cozii.html"]:
    subprocess.run([PY, "-X", "utf8", "../raport_executiv_2026-11/lint_numbers.py", h])
