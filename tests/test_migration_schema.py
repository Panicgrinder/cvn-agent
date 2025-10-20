import unittest
import tempfile
import os
import json
import sys


class TestMigrationSchema(unittest.TestCase):
    """Tests für das Dataset-Schema-Migrationsskript."""
    
    def setUp(self):
        # Projekt-Root zum Python-Pfad hinzufügen
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if project_root not in sys.path:
            sys.path.insert(0, project_root)
    
    def test_migrate_old_to_new_schema(self):
        """Test der Migration von altem (prompt, must_include) zu neuem Schema (messages, checks)."""
        from scripts.migrate_dataset_schemas import migrate_demo_dataset

        # Erstelle temporäres Dataset im alten Format
        old_data: list[dict[str, object]] = [
            {"id": "eval-001", "prompt": "Test prompt 1", "must_include": ["term1", "term2"]},
            {"id": "eval-002", "prompt": "Test prompt 2", "must_include": ["term3"]},
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            # Simuliere eval/datasets Struktur
            datasets_dir = os.path.join(tmp_dir, "eval", "datasets")
            os.makedirs(datasets_dir, exist_ok=True)

            # Schreibe alte Datei
            old_file = os.path.join(datasets_dir, "eval-21-40_fantasy_v1.0.json")
            with open(old_file, "w", encoding="utf-8") as f:
                for item in old_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

            # Ändere Arbeitsverzeichnis für migrate_demo_dataset
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                success = migrate_demo_dataset()
                self.assertTrue(success, "Migration sollte erfolgreich sein")

                # Prüfe migrierte Datei
                with open(old_file, "r", encoding="utf-8") as f:
                    migrated_lines = [json.loads(line) for line in f if line.strip()]

                self.assertEqual(len(migrated_lines), 2)

                # Prüfe erstes Item
                item1 = migrated_lines[0]
                self.assertEqual(item1["id"], "eval-001")
                self.assertIn("messages", item1)
                self.assertIn("checks", item1)
                self.assertEqual(item1["messages"], [{"role": "user", "content": "Test prompt 1"}])
                self.assertEqual(item1["checks"]["must_include"], ["term1", "term2"])
                self.assertNotIn("prompt", item1)
                self.assertNotIn("must_include", item1)

                # Prüfe Backup
                backup_file = old_file + ".backup"
                self.assertTrue(os.path.exists(backup_file), "Backup sollte existieren")

            finally:
                os.chdir(original_cwd)
    
    def test_migration_idempotent(self):
        """Test dass bereits migrierte Dateien nicht nochmals verändert werden."""
        from scripts.migrate_dataset_schemas import migrate_demo_dataset

        # Erstelle bereits migrierte Daten
        new_data: list[dict[str, object]] = [
            {
                "id": "eval-001",
                "messages": [{"role": "user", "content": "New format"}],
                "checks": {"must_include": ["term1"]},
            }
        ]

        with tempfile.TemporaryDirectory() as tmp_dir:
            datasets_dir = os.path.join(tmp_dir, "eval", "datasets")
            os.makedirs(datasets_dir, exist_ok=True)

            new_file = os.path.join(datasets_dir, "eval-21-40_fantasy_v1.0.json")
            with open(new_file, "w", encoding="utf-8") as f:
                for item in new_data:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")

            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                success = migrate_demo_dataset()
                self.assertTrue(success, "Migration von bereits migrierten Daten sollte erfolgreich sein")

                # Datei sollte unverändert bleiben
                with open(new_file, "r", encoding="utf-8") as f:
                    unchanged_lines = [json.loads(line) for line in f if line.strip()]

                self.assertEqual(len(unchanged_lines), 1)
                self.assertEqual(unchanged_lines[0], new_data[0])

            finally:
                os.chdir(original_cwd)
    
    def test_migration_empty_file_handling(self):
        """Test dass leere Dateien korrekt behandelt werden."""
        from scripts.migrate_dataset_schemas import migrate_demo_dataset
        
        with tempfile.TemporaryDirectory() as tmp_dir:
            datasets_dir = os.path.join(tmp_dir, "eval", "datasets")
            os.makedirs(datasets_dir, exist_ok=True)
            
            # Erstelle leere Datei
            empty_file = os.path.join(datasets_dir, "eval-21-40_fantasy_v1.0.json")
            with open(empty_file, "w", encoding="utf-8") as f:
                _ = f.write("")  # Leere Datei bewusst
            
            original_cwd = os.getcwd()
            try:
                os.chdir(tmp_dir)
                success = migrate_demo_dataset()
                self.assertFalse(success, "Migration einer leeren Datei sollte fehlschlagen")
                
            finally:
                os.chdir(original_cwd)


if __name__ == "__main__":
    unittest.main()
