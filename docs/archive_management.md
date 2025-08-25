# Archive Directory Management Guidelines

This document outlines the conventions and best practices for managing files within the `archive` directory. The purpose of this directory is to store historical versions of code, completed projects, or any files that are no longer actively used in development but need to be preserved for reference or rollback.

## Directory Structure

The `archive` directory is organized using dated subdirectories. Each subdirectory corresponds to a specific project, milestone, or a set of related files that were completed or replaced at a specific point in time.

### Naming Convention for Subdirectories

Subdirectories within `archive` should follow this naming convention:
```
DT<YYMMDD>_<descriptive_title>
```
- `DT`: Prefix indicating a date-tagged archive.
- `<YYMMDD>`: The date (Year, Month, Day) when the files were archived or the project was completed. Use the ISO 8601 date format (e.g., 250823 for August 23, 2025).
- `<descriptive_title>`: A short, descriptive name for the project or set of files, using only lowercase letters, numbers, and underscores. This should clearly indicate the content or purpose of the archived materials.

**Example**:
- `DT250823_esp32_web_control_demo`: Contains files related to the initial ESP32 web control demo project completed on August 23, 2025.

## File Management

1.  **Active Development Files**: Files that are currently being developed, tested, or used should reside in the project's root directory or other appropriate active development directories (e.g., `src`, `tests`).
2.  **Archiving Process**:
    *   When a version of a file or a set of files is superseded by a new version, or when a project phase is completed, the old files should be moved to a new or existing appropriately named subdirectory within `archive`.
    *   If a file with the same name already exists in the target archive subdirectory, it indicates a conflict. In this case:
        *   If the content is identical, no action is needed.
        *   If the content is different, the file being archived should be renamed to reflect its version or stage before moving (e.g., `esp32_web_control_demo_v1.py`, `esp32_web_control_demo_before_api_refactor.py`).
3.  **Root `archive` Directory**: The root of the `archive` directory should not contain loose files. All archived files must be placed within a dated subdirectory to maintain organization.

## Best Practices

-   **Consistency**: Always follow the `DT<YYMMDD>_<title>` naming convention for new archive subdirectories.
-   **Documentation**: If an archived set of files is significant, consider adding a brief `README.md` file within the subdirectory to explain its contents and context.
-   **Regular Review**: Periodically review the `archive` directory to ensure it remains organized and relevant. Old or redundant archives can be deleted if they are no longer needed.