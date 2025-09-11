#!/usr/bin/env python3
import argparse, os, subprocess, tempfile, shutil, sys, pandas as pd, csv, pathlib

def run_cmd(cmd, cwd=None):
    print("CMD:", " ".join(cmd))
    subprocess.run(cmd, check=True, cwd=cwd)

def clone_repo(clone_url, dest_dir):
    run_cmd(["git","clone","--depth","1", clone_url, dest_dir])

def run_ck(ck_jar_path, project_dir, output_dir, use_jars="false", max_files="0", variables_and_fields="false"):
    os.makedirs(output_dir, exist_ok=True)
    cmd = ["java","-jar", ck_jar_path, project_dir, use_jars, max_files, variables_and_fields, output_dir]
    run_cmd(cmd)

def find_csv(output_dir):
    # CK normalmente gera class.csv, method.csv, variable.csv inside output_dir
    candidates = []
    for name in os.listdir(output_dir):
        if name.lower().startswith("class") and name.lower().endswith(".csv"):
            return os.path.join(output_dir, name)
    # fallback
    for name in os.listdir(output_dir):
        if name.endswith(".csv"):
            candidates.append(os.path.join(output_dir,name))
    return candidates[0] if candidates else None

def summarize_class_csv(class_csv_path, out_summary_csv):
    df = pd.read_csv(class_csv_path)
    # metrics we care about (some may be missing; handle gracefully)
    metrics = ['cbo','dit','lcom','lcom*','wmc','loc']
    rows = []
    for m in metrics:
        if m in df.columns:
            col = pd.to_numeric(df[m], errors='coerce').dropna()
            if len(col)==0:
                continue
            rows.append({
                'metric': m,
                'count': len(col),
                'mean': float(col.mean()),
                'median': float(col.median()),
                'std': float(col.std()),
                'min': float(col.min()),
                'max': float(col.max())
            })
    if rows:
        pd.DataFrame(rows).to_csv(out_summary_csv, index=False)
        print("Summary written to", out_summary_csv)
    else:
        print("No matching metric columns found in", class_csv_path)

def main():
    p = argparse.ArgumentParser()
    p.add_argument("--repo", required=True, help="owner/repo or full https git url")
    p.add_argument("--ck", required=True, help="path to ck-...jar")
    p.add_argument("--outdir", default="docs/results", help="where to save outputs")
    args = p.parse_args()

    ck_jar = args.ck
    outdir = args.outdir
    repo = args.repo.strip()

    # normalize clone URL
    if repo.startswith("http://") or repo.startswith("https://") or repo.endswith(".git"):
        clone_url = repo
        shortname = os.path.splitext(os.path.basename(clone_url))[0]
    else:
        clone_url = f"https://github.com/{repo}.git"
        shortname = repo.replace("/","_")

    tmpdir = tempfile.mkdtemp(prefix="lab02_")
    proj_dir = os.path.join(tmpdir, shortname)
    try:
        print("Cloning", clone_url, "->", proj_dir)
        clone_repo(clone_url, proj_dir)

        ck_out = os.path.join(tmpdir, "ck_out")
        print("Running CK ...")
        run_ck(ck_jar, proj_dir, ck_out, use_jars="false", max_files="0", variables_and_fields="false")

        class_csv = find_csv(ck_out)
        if not class_csv:
            print("ERROR: class csv not found in", ck_out)
            sys.exit(1)

        os.makedirs(outdir, exist_ok=True)
        raw_dest = os.path.join(outdir, f"metricas_raw_{shortname}.csv")
        shutil.copy(class_csv, raw_dest)
        print("Raw class CSV copied to", raw_dest)

        summary_dest = os.path.join(outdir, f"metricas_summary_{shortname}.csv")
        summarize_class_csv(raw_dest, summary_dest)

    finally:
        # cleanup repo (keep results)
        print("Cleaning up temporary clone:", tmpdir)
        shutil.rmtree(tmpdir, ignore_errors=True)

if __name__ == "__main__":
    main()
