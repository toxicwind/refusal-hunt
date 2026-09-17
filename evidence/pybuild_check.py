#!/usr/bin/env python3
"""Python/build health check — full stdout/stderr captured per check."""
import json, os, subprocess, sys, time, tempfile

OUT = os.path.expanduser("~/workspace/refusal-hunt/evidence/pybuild-check-result.json")
VENV = os.path.expanduser("~/workspace/venvs/pybuild-check-20260916")
FORENSICS_PY = os.path.expanduser("~/workspace/venvs/forensics/bin/python")
results = []

def run(name, cmd, timeout=240, env=None):
    t0 = time.time()
    try:
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, env=env)
        rc, so, se = p.returncode, p.stdout, p.stderr
        err = ""
    except subprocess.TimeoutExpired as e:
        rc, so, se = -99, e.stdout or "", e.stderr or ""
        err = "TIMEOUT"
    except Exception as e:
        rc, so, se, err = -98, "", "", repr(e)
    results.append({
        "check": name, "cmd": cmd if isinstance(cmd, str) else " ".join(cmd),
        "returncode": rc, "elapsed_s": round(time.time() - t0, 3),
        "stdout": so, "stderr": se, "error": err,
    })
    return rc

# 1. system python identity
run("python_version", [sys.executable, "--version"])
run("pip_version", [sys.executable, "-m", "pip", "--version"])

# 2. pip check (system)
run("pip_check_system", [sys.executable, "-m", "pip", "check"])

# 3. fresh durable venv
run("venv_create", [sys.executable, "-m", "venv", VENV], timeout=300)
vpip = os.path.join(VENV, "bin", "pip")
vpy = os.path.join(VENV, "bin", "python")
run("venv_pip_version", [vpip, "--version"])
run("venv_pip_check", [vpip, "check"])

# 4. real package install + import in fresh venv
run("venv_pip_install_six", [vpip, "install", "six"], timeout=300)
run("venv_import_six", [vpy, "-c", "import six; print('six', six.__version__)"])

# 5. compiler
run("cc_version", ["cc", "--version"])
with tempfile.TemporaryDirectory() as td:
    src = os.path.join(td, "hello.c")
    exe = os.path.join(td, "hello")
    with open(src, "w") as f:
        f.write('int main(void){return 0;}\n')
    run("cc_compile_hello", ["cc", "-o", exe, src])
    run("cc_run_hello", [exe])

# 6. setuptools/wheel presence
run("setuptools_wheel_system", [sys.executable, "-c",
    "import setuptools, wheel; print('setuptools', setuptools.__version__, 'wheel', wheel.__version__)"])
run("setuptools_wheel_venv", [vpy, "-c",
    "import setuptools; print('setuptools', setuptools.__version__)"])

# 7. pyarrow/pandas/tiktoken imports (forensics venv)
run("import_pyarrow", [FORENSICS_PY, "-c", "import pyarrow; print('pyarrow', pyarrow.__version__)"])
run("import_pandas", [FORENSICS_PY, "-c", "import pandas; print('pandas', pandas.__version__)"])
run("import_tiktoken", [FORENSICS_PY, "-c", "import tiktoken; print('tiktoken', tiktoken.__version__)"])

# 8. three-row zstd parquet round trip
run("parquet_roundtrip", [FORENSICS_PY, "-c", """
import pyarrow as pa, pyarrow.parquet as pq, os
p = os.path.expanduser('~/workspace/refusal-hunt/evidence/pybuild-roundtrip.parquet')
t = pa.table({'a':[1,2,3],'b':['x','y','z'],'c':[1.1,2.2,3.3]})
pq.write_table(t, p, compression='zstd')
t2 = pq.read_table(p)
assert t2.num_rows == 3 and t2.num_columns == 3
assert t2.column('a').to_pylist() == [1,2,3]
print('roundtrip OK', t2.num_rows, 'rows x', t2.num_columns, 'cols')
"""])

with open(OUT, "w") as f:
    json.dump({"generated_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()), "checks": results}, f, indent=1)
print("wrote", OUT, len(results), "checks")
