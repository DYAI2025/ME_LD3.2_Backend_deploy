#!/usr/bin/env python3
"""
Import 127 validated markers into MongoDB
"""

import os
import sys
import json
import asyncio
from datetime import datetime
from typing import List, Dict, Any
from pymongo import MongoClient
from pymongo.errors import BulkWriteError
import argparse

# MongoDB connection
MONGODB_URI = os.getenv("MONGODB_URI", "mongodb://localhost:27017")
DATABASE_NAME = "marker_engine"
COLLECTION_NAME = "markers"

def load_markers_from_file(filepath: str) -> List[Dict]:
    """Load markers from JSON or YAML file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        if filepath.endswith('.json'):
            return json.load(f)
        elif filepath.endswith('.yaml') or filepath.endswith('.yml'):
            import yaml
            return yaml.safe_load(f)
        else:
            # Try JSON first
            try:
                return json.load(f)
            except:
                import yaml
                return yaml.safe_load(f)

def validate_marker(marker: Dict) -> bool:
    """Validate marker structure"""
    required_fields = ['marker_id', 'level', 'pattern']
    return all(field in marker for field in required_fields)

def enrich_marker(marker: Dict) -> Dict:
    """Add metadata to marker"""
    marker['created_at'] = datetime.utcnow()
    marker['updated_at'] = datetime.utcnow()
    marker['version'] = "1.0.0"
    marker['status'] = 'active'
    
    # Ensure proper types
    if 'confidence_threshold' not in marker:
        marker['confidence_threshold'] = 0.7
    
    if 'dependencies' not in marker:
        marker['dependencies'] = []
    
    if 'metadata' not in marker:
        marker['metadata'] = {}
    
    return marker

def import_markers(markers: List[Dict], mongodb_uri: str = None, dry_run: bool = False):
    """Import markers into MongoDB"""
    
    if dry_run:
        print("🔍 DRY RUN MODE - No data will be written")
    
    # Validate all markers
    valid_markers = []
    invalid_markers = []
    
    for i, marker in enumerate(markers):
        if validate_marker(marker):
            valid_markers.append(enrich_marker(marker))
        else:
            invalid_markers.append((i, marker))
    
    print(f"✅ Valid markers: {len(valid_markers)}")
    print(f"❌ Invalid markers: {len(invalid_markers)}")
    
    if invalid_markers:
        print("\n⚠️ Invalid markers found:")
        for idx, marker in invalid_markers[:5]:  # Show first 5
            print(f"  - Index {idx}: {marker.get('marker_id', 'NO_ID')}")
    
    if not valid_markers:
        print("❌ No valid markers to import")
        return
    
    if dry_run:
        print("\n📋 Sample markers to be imported:")
        for marker in valid_markers[:3]:
            print(f"  - {marker['marker_id']} ({marker['level']}): {marker.get('description', 'No description')}")
        return
    
    # Connect to MongoDB
    try:
        client = MongoClient(mongodb_uri or MONGODB_URI)
        db = client[DATABASE_NAME]
        collection = db[COLLECTION_NAME]
        
        # Test connection
        client.admin.command('ping')
        print(f"✅ Connected to MongoDB")
        
        # Create indexes
        collection.create_index("marker_id", unique=True)
        collection.create_index("level")
        collection.create_index("status")
        collection.create_index([("created_at", -1)])
        print(f"✅ Indexes created")
        
        # Import markers with upsert
        operations = []
        for marker in valid_markers:
            operations.append({
                'update_one': {
                    'filter': {'marker_id': marker['marker_id']},
                    'update': {'$set': marker},
                    'upsert': True
                }
            })
        
        # Bulk write
        if operations:
            result = collection.bulk_write(operations)
            print(f"\n📊 Import Results:")
            print(f"  - Inserted: {result.upserted_count}")
            print(f"  - Modified: {result.modified_count}")
            print(f"  - Total processed: {len(operations)}")
            
            # Verify
            total_count = collection.count_documents({})
            print(f"  - Total markers in DB: {total_count}")
            
            # Show sample
            print(f"\n📋 Sample markers in database:")
            for marker in collection.find().limit(3):
                print(f"  - {marker['marker_id']} ({marker['level']})")
        
        print(f"\n✅ Import completed successfully!")
        
    except Exception as e:
        print(f"❌ Error importing markers: {e}")
        raise

def main():
    parser = argparse.ArgumentParser(description='Import markers into MongoDB')
    parser.add_argument('--file', '-f', required=True, help='Path to markers file (JSON or YAML)')
    parser.add_argument('--mongodb-uri', '-m', help='MongoDB connection URI')
    parser.add_argument('--dry-run', '-d', action='store_true', help='Validate without importing')
    parser.add_argument('--sample', '-s', action='store_true', help='Create sample markers file')
    
    args = parser.parse_args()
    
    if args.sample:
        # Create sample markers file
        sample_markers = [
            {
                "marker_id": "A_TE_",
                "level": "ATO",
                "pattern": r"\b(test|testing|tested)\b",
                "description": "Test/Testing marker",
                "category": "action",
                "confidence_threshold": 0.8
            },
            {
                "marker_id": "A_TH_",
                "level": "ATO",
                "pattern": r"\b(think|thinking|thought)\b",
                "description": "Thinking/Thought marker",
                "category": "cognitive",
                "confidence_threshold": 0.8
            },
            {
                "marker_id": "S_QU_",
                "level": "SEM",
                "pattern": r"\?|^(what|when|where|why|how|who)",
                "description": "Question marker",
                "category": "interrogative",
                "confidence_threshold": 0.9,
                "dependencies": []
            },
            # Add more sample markers as needed
        ]
        
        with open('sample_markers.json', 'w') as f:
            json.dump(sample_markers, f, indent=2)
        print("✅ Sample markers file created: sample_markers.json")
        return
    
    # Load markers from file
    if not os.path.exists(args.file):
        print(f"❌ File not found: {args.file}")
        sys.exit(1)
    
    try:
        markers = load_markers_from_file(args.file)
        if isinstance(markers, dict) and 'markers' in markers:
            markers = markers['markers']
        
        print(f"📂 Loaded {len(markers)} markers from {args.file}")
        
        # Import markers
        import_markers(markers, args.mongodb_uri, args.dry_run)
        
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()