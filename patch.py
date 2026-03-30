import re

def fix_file(filepath, pattern, replacement):
    with open(filepath, 'r') as f:
        content = f.read()

    new_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)

    with open(filepath, 'w') as f:
        f.write(new_content)

main_pattern = r"artifacts_dir=Path\(settings\.artifact_dir\)\s*/ settings\.table_conversion_artifacts_subdir,"
main_replacement = r"artifacts_dir=(Path(settings.artifact_dir) / settings.table_conversion_artifacts_subdir).as_posix(),"

spread_pattern = r"artifacts_dir=Path\(settings\.artifact_dir\)\s*/ settings\.cell_error_artifacts_subdir,"
spread_replacement = r"artifacts_dir=(Path(settings.artifact_dir) / settings.cell_error_artifacts_subdir).as_posix(),"

fix_file("foil-serve_repo/src/foil_serve/main.py", main_pattern, main_replacement)
fix_file("foil-serve_repo/src/foil_serve/spreadsheet.py", spread_pattern, spread_replacement)
