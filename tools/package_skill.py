"""Package the omega-engineering-x10 router as a standalone skill ZIP for the claude.ai Skills uploader.

  python3 tools/package_skill.py [--out dist]     build dist/omega-engineering-x10.zip, then verify it
  python3 tools/package_skill.py --verify <zip>   verify any skill ZIP before uploading it

The uploader takes one skill folder per ZIP and rejects symbolic links ("Zip file contains a symbolic
link"). Zipping the repository (or GitHub's "Download ZIP") stores plugins/mattpocock-skills/AGENTS.md
as a link and puts eleven entries at the top level, so it can never be uploaded as a skill. This
script stages an allowlist of omega-core files as regular files instead. A link is replaced by the
contents of its target, and refused if the target is outside the repository. The repository is
only read.

In the plugin, SKILL.md reaches scripts/ and registry/ through ../../; in the ZIP they sit next to
SKILL.md, so the staged copy's paths are rewritten (SKILL_REWRITES). The full marketplace is not a
skill: install it with `claude plugin marketplace add` (docs/INSTALL.md).
"""
import argparse
import os
import re
import shutil
import stat
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CORE = ROOT / "plugins" / "omega-core"
NAME = "omega-engineering-x10"

# path inside the skill folder -> source file
FILES = {
    "SKILL.md": CORE / "skills" / NAME / "SKILL.md",
    "LICENSE": CORE / "LICENSE",
    "scripts/omega.py": CORE / "scripts" / "omega.py",
    "scripts/install-plugin-deps.sh": CORE / "scripts" / "install-plugin-deps.sh",
    "registry/skills.json": CORE / "registry" / "skills.json",
    "registry/capabilities.json": CORE / "registry" / "capabilities.json",
    "registry/routing-rules.json": CORE / "registry" / "routing-rules.json",
}

SKILL_REWRITES = [
    ("`../../registry/", "`registry/"),
    ("`../../scripts/omega.py`", "`scripts/omega.py`"),
    ("<base>/../../scripts/omega.py", "<base>/scripts/omega.py"),
    ("3. **Check it is installed.** Each plugin is installed separately.",
     "3. **Check it is installed.** Each plugin is installed separately. When this skill runs as an\n"
     "   uploaded skill outside Claude Code (claude.ai), plugins cannot be installed there: say the\n"
     "   specialist is unavailable in this surface, name it, and use the route's fallback."),
]

FORBIDDEN = re.compile(r"(^|/)(\.git|node_modules|__pycache__|\.cache|\.venv|\.env[^/]*|\.DS_Store)(/|$)")
SECRET = re.compile(rb"(AKIA[0-9A-Z]{16}|ghp_[A-Za-z0-9]{20,}|github_pat_|sk-(ant|or|proj)-[A-Za-z0-9-]{10,}"
                    rb"|xox[abpr]-|AIza[0-9A-Za-z_-]{30,}|-----BEGIN [A-Z ]*PRIVATE KEY)")


def stage(dest):
    """Copy FILES into dest/NAME as regular files; return the skill folder."""
    folder = dest / NAME
    for rel, src in FILES.items():
        real = Path(os.path.realpath(src))
        if not real.is_relative_to(ROOT):
            raise SystemExit(f"refused: {src} resolves outside the repository ({real})")
        data = real.read_bytes()
        if rel == "SKILL.md":
            text = data.decode()
            for old, new in SKILL_REWRITES:
                if old not in text:
                    raise SystemExit(f"SKILL.md changed upstream of the packager; anchor not found: {old!r}")
                text = text.replace(old, new)
            if "../../" in text:
                raise SystemExit("staged SKILL.md still references files outside the skill folder")
            data = text.encode()
        out = folder / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_bytes(data)
        out.chmod(0o755 if os.access(real, os.X_OK) else 0o644)
    return folder


def write_zip(folder, zpath):
    with zipfile.ZipFile(zpath, "w", zipfile.ZIP_DEFLATED) as z:
        for p in sorted(folder.rglob("*")):
            if p.is_symlink():
                raise SystemExit(f"symlink in staging: {p}")
            if p.is_file():
                # fixed timestamp so rebuilding unchanged sources gives the same bytes
                info = zipfile.ZipInfo(f"{folder.name}/{p.relative_to(folder).as_posix()}", (2026, 1, 1, 0, 0, 0))
                info.compress_type = zipfile.ZIP_DEFLATED
                info.create_system = 3
                info.external_attr = (stat.S_IFREG | (p.stat().st_mode & 0o777)) << 16
                z.writestr(info, p.read_bytes())


def verify(zpath):
    """Return a list of problems that would make the uploader reject the ZIP (empty = OK)."""
    problems = []
    with zipfile.ZipFile(zpath) as z:
        infos = z.infolist()
        names = [i.filename for i in infos]
        for i in infos:
            # Unix mode in the high 16 bits; many tools write permissions only (file type 0) for plain files
            ftype = stat.S_IFMT(i.external_attr >> 16)
            if ftype == stat.S_IFLNK:
                problems.append(f"symbolic link: {i.filename}")
            elif ftype not in (0, stat.S_IFREG, stat.S_IFDIR):
                problems.append(f"not a regular file: {i.filename}")
            if i.filename.startswith("/") or ".." in i.filename.split("/") or "\\" in i.filename:
                problems.append(f"unsafe path: {i.filename}")
            if FORBIDDEN.search(i.filename):
                problems.append(f"excluded content: {i.filename}")
            if not i.is_dir() and SECRET.search(z.read(i)):
                problems.append(f"secret-like string: {i.filename}")
        tops = sorted({n.split("/")[0] for n in names})
        if len(tops) != 1:
            return problems + [f"expected one skill folder at the top level, found {len(tops)}: {tops[:5]}"]
        top = tops[0]
        if f"{top}/SKILL.md" not in names:
            return problems + [f"{top}/SKILL.md missing"]
        text = z.read(f"{top}/SKILL.md").decode("utf-8")
    m = re.match(r"---\n(.*?)\n---\n", text, re.S)
    if not m:
        return problems + ["SKILL.md has no YAML frontmatter"]
    fm = dict(re.findall(r"^([a-z_-]+):[ \t]*(.*)$", m.group(1), re.M))
    name, desc = fm.get("name", ""), fm.get("description", "")
    if not re.fullmatch(r"[a-z0-9-]{1,64}", name):
        problems.append(f"frontmatter name {name!r}: needs 1-64 lowercase letters, digits or hyphens")
    elif name != top:
        problems.append(f"frontmatter name {name!r} differs from folder {top!r}")
    if not 0 < len(desc) <= 1024:
        problems.append(f"frontmatter description is {len(desc)} characters (1-1024 allowed)")
    if re.search(r"[<>]", name + desc):
        problems.append("angle brackets in frontmatter name/description")
    for ref in re.findall(r"`((?:scripts|registry)/[^`\s]+)`", text):
        if f"{top}/{ref}" not in names:
            problems.append(f"SKILL.md references {ref}, which is not in the ZIP")
    return problems


def main():
    ap = argparse.ArgumentParser(description=__doc__.split("\n")[0])
    ap.add_argument("--out", default=str(ROOT / "dist"), help="output directory (default: dist/)")
    ap.add_argument("--verify", metavar="ZIP", help="only verify an existing ZIP")
    a = ap.parse_args()
    if a.verify:
        zpath = Path(a.verify)
    else:
        out = Path(a.out).resolve()
        out.mkdir(parents=True, exist_ok=True)
        zpath = out / f"{NAME}.zip"
        with tempfile.TemporaryDirectory() as tmp:
            write_zip(stage(Path(tmp)), zpath)
    problems = verify(zpath)
    for p in problems:
        print(f"FAIL {p}")
    if problems:
        return 1
    print(f"OK {zpath} ({zpath.stat().st_size} bytes): one skill folder, no symbolic links, valid SKILL.md")
    return 0


if __name__ == "__main__":
    sys.exit(main())
