import sys
import requests
import traceback
from app import create_app
from extensions import db

app = create_app()

def run_tests():
    with app.test_client() as client:
        with app.app_context():
            print("Checking all GET routes for basic 200/302 status (no 500s)...")
            rules = [rule for rule in app.url_map.iter_rules() if 'GET' in rule.methods]
            errors = []
            for rule in rules:
                # skip routes with arguments for now, just hit base paths
                if '<' not in str(rule):
                    path = str(rule)
                    try:
                        resp = client.get(path)
                        if resp.status_code == 500:
                            errors.append(f"500 Internal Error on {path}")
                        else:
                            print(f"OK: {path} -> {resp.status_code}")
                    except Exception as e:
                        errors.append(f"Exception on {path}: {str(e)}")
            
            if errors:
                print("\nERRORS FOUND:")
                for e in errors:
                    print(e)
            else:
                print("\nNo 500 errors found on base GET routes!")

if __name__ == '__main__':
    run_tests()
