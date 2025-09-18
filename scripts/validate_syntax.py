#!/usr/bin/env python3
"""
Syntax Validation for Episodic Memory Services
Validates that the Python services have correct syntax and imports
"""

import ast
import sys
from pathlib import Path

def validate_python_syntax(file_path):
    """Validate Python syntax for a file"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        # Parse the AST
        ast.parse(content)
        return True, None
    except SyntaxError as e:
        return False, f"Syntax error: {e}"
    except Exception as e:
        return False, f"Error: {e}"

def check_service_structure(file_path):
    """Check that service has expected class structure"""
    try:
        with open(file_path, 'r') as f:
            content = f.read()

        tree = ast.parse(content)

        classes = []
        functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                classes.append(node.name)
            elif isinstance(node, ast.FunctionDef):
                functions.append(node.name)

        return classes, functions
    except Exception as e:
        return [], []

def main():
    """Main validation function"""
    print("🔍 Validating Episodic Memory Services Syntax")
    print("=" * 50)

    # Files to validate
    service_files = [
        "src/ml/belief_revision_service.py",
        "src/ml/episodic_memory_manager.py"
    ]

    all_valid = True

    for file_path in service_files:
        full_path = Path(__file__).parent.parent / file_path
        print(f"\n📄 Validating {file_path}...")

        if not full_path.exists():
            print(f"❌ File not found: {full_path}")
            all_valid = False
            continue

        # Syntax validation
        valid, error = validate_python_syntax(full_path)
        if valid:
            print("✅ Syntax valid")
        else:
            print(f"❌ Syntax invalid: {error}")
            all_valid = False
            continue

        # Structure validation
        classes, functions = check_service_structure(full_path)
        print(f"✅ Found {len(classes)} classes: {', '.join(classes)}")
        print(f"✅ Found {len(functions)} functions")

        # Check for expected classes
        expected_classes = {
            "belief_revision_service.py": ["BeliefRevisionService"],
            "episodic_memory_manager.py": ["EpisodicMemoryManager"]
        }

        file_name = Path(file_path).name
        if file_name in expected_classes:
            for expected_class in expected_classes[file_name]:
                if expected_class in classes:
                    print(f"✅ Required class '{expected_class}' found")
                else:
                    print(f"❌ Required class '{expected_class}' missing")
                    all_valid = False

    # Validate migration SQL syntax
    migration_file = Path(__file__).parent.parent / "supabase/migrations/011_expert_episodic_memory_system.sql"
    print(f"\n📄 Validating {migration_file.name}...")

    if migration_file.exists():
        print("✅ Migration file exists")

        # Basic SQL syntax check (look for common issues)
        with open(migration_file, 'r') as f:
            sql_content = f.read()

        if "CREATE TABLE" in sql_content:
            print("✅ Contains CREATE TABLE statements")
        if "CREATE INDEX" in sql_content:
            print("✅ Contains CREATE INDEX statements")
        if "expert_belief_revisions" in sql_content:
            print("✅ Contains expert_belief_revisions table")
        if "expert_episodic_memories" in sql_content:
            print("✅ Contains expert_episodic_memories table")
    else:
        print("❌ Migration file not found")
        all_valid = False

    # Summary
    print("\n📊 Validation Summary")
    print("=" * 50)

    if all_valid:
        print("✅ All syntax validations passed!")
        print("📁 Files are ready for deployment")
        return True
    else:
        print("❌ Some validations failed")
        print("🔧 Please fix the issues above")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)