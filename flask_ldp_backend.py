from flask import Flask, request, jsonify
from flask_cors import CORS
from pymongo import MongoClient
from bson import ObjectId
import os
from datetime import datetime
import json
import math

from flask import Flask, render_template

app = Flask(__name__)
CORS(app) 

@app.route('/')
def index():
    return render_template('full.html')




 # Enable CORS for all routes

# MongoDB configuration
MONGO_URI = "mongodb+srv://maxdot786:debugger123@cluster0.kjgnmvp.mongodb.net/?retryWrites=true&w=majority&appName=Cluster0"
DATABASE_NAME = "testdb"
COLLECTION_NAME = "data"

# Initialize MongoDB client
try:
    client = MongoClient(MONGO_URI)
    db = client[DATABASE_NAME]
    collection = db[COLLECTION_NAME]
    print(f"Connected to MongoDB: {DATABASE_NAME}.{COLLECTION_NAME}")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    client = None
    db = None
    collection = None


class JSONEncoder(json.JSONEncoder):
    """Custom JSON encoder for MongoDB ObjectId"""
    def default(self, obj):
        if isinstance(obj, ObjectId):
            return str(obj)
        return super().default(obj)

app.json_encoder = JSONEncoder


def sanitize_document(doc):
    """Replace NaN/Infinity values with safe defaults so JSON is valid"""
    for k, v in doc.items():
        if isinstance(v, float):
            if math.isnan(v) or math.isinf(v):
                doc[k] = None  # Use None (becomes null in JSON)
    return doc


@app.route('/', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'LDP Quote Tool API is running',
        'mongodb_connected': collection is not None
    })


@app.route('/api/sites', methods=['GET'])
def get_sites():
    """Get all sites from MongoDB"""
    try:
        if collection is None:
            return jsonify({'error': 'Database connection not available'}), 500

        sites = []
        for site in collection.find():
            site = sanitize_document(site)
            if '_id' in site:
                site['_id'] = str(site['_id'])
            sites.append(site)

        print(f"Retrieved {len(sites)} sites from database")
        return jsonify(sites)

    except Exception as e:
        print(f"Error retrieving sites: {e}")
        return jsonify({'error': 'Failed to retrieve sites'}), 500


@app.route('/api/sites', methods=['POST'])
def create_site():
    """Create a new site entry (from external form submissions)"""
    try:
        if collection is None:
            return jsonify({'error': 'Database connection not available'}), 500

        data = request.get_json()

        new_site = {
            'Date': datetime.now().strftime('%m/%d/%Y'),
            'Record Number': f"EXT{datetime.now().strftime('%Y%m%d%H%M%S')}",
            'Record Type': 'External Quote Request',
            'Department': 'Land Development Partners',
            'Short Notes': data.get('notes', ''),
            'Project Description': f"{data.get('jobType', 'Unknown')} - {data.get('materialDesc', 'Material not specified')}",
            'Application Status': 'New Quote Request',
            'Work Location': data.get('projectLocation', ''),
            'URL': '',

            # Additional fields from the form
            'Job Type': data.get('jobType', ''),
            'Region': data.get('region', ''),
            'Quantity': data.get('quantity', 0),
            'Material Description': data.get('materialDesc', ''),
            'Expansion Index': data.get('expansionIndex', ''),
            'Rock Type': data.get('rock', ''),
            'Truck Type': data.get('truckType', ''),
            'Budget': data.get('budget', 0),
            'Dump Fee': data.get('dumpFee', 0),
            'LDP Fee': data.get('ldpFee', 0),
            'Estimated Start': data.get('estimatedStart', ''),
            'Project City': data.get('projectCity', ''),
            'Project State': data.get('projectState', ''),
            'Project Zip': data.get('projectZip', ''),
            'Parcel Number': data.get('parcelNo', ''),
            'Entry Type': data.get('entryType', 'external'),
            'Created At': datetime.utcnow().isoformat(),
            'Contact Name': data.get('contactName', ''),
            'Contact Phone': data.get('contactPhone', ''),
            'Contact Email': data.get('contactEmail', ''),
            'Company': data.get('company', '')
        }

        new_site = sanitize_document(new_site)
        result = collection.insert_one(new_site)

        new_site['_id'] = str(result.inserted_id)

        print(f"Created new external site entry: {result.inserted_id}")
        return jsonify({
            'success': True,
            'id': str(result.inserted_id),
            'message': 'Site entry created successfully',
            'data': new_site
        }), 201

    except Exception as e:
        print(f"Error creating site: {e}")
        return jsonify({'error': 'Failed to create site entry'}), 500


@app.route('/api/sites/<site_id>', methods=['GET'])
def get_site(site_id):
    """Get a specific site by ID"""
    try:
        if collection is None:
            return jsonify({'error': 'Database connection not available'}), 500

        object_id = ObjectId(site_id)
        site = collection.find_one({'_id': object_id})

        if site:
            site = sanitize_document(site)
            site['_id'] = str(site['_id'])
            return jsonify(site)
        else:
            return jsonify({'error': 'Site not found'}), 404

    except Exception as e:
        print(f"Error retrieving site {site_id}: {e}")
        return jsonify({'error': 'Failed to retrieve site'}), 500


@app.route('/api/sites/<site_id>', methods=['PUT'])
def update_site(site_id):
    """Update a specific site"""
    try:
        if collection is None:
            return jsonify({'error': 'Database connection not available'}), 500

        data = request.get_json()
        object_id = ObjectId(site_id)

        data['Updated At'] = datetime.utcnow().isoformat()
        data = sanitize_document(data)

        result = collection.update_one(
            {'_id': object_id},
            {'$set': data}
        )

        if result.matched_count:
            return jsonify({
                'success': True,
                'message': 'Site updated successfully',
                'modified_count': result.modified_count
            })
        else:
            return jsonify({'error': 'Site not found'}), 404

    except Exception as e:
        print(f"Error updating site {site_id}: {e}")
        return jsonify({'error': 'Failed to update site'}), 500


@app.route('/api/sites/<site_id>', methods=['DELETE'])
def delete_site(site_id):
    """Delete a specific site"""
    try:
        if collection is None:
            return jsonify({'error': 'Database connection not available'}), 500

        object_id = ObjectId(site_id)
        result = collection.delete_one({'_id': object_id})

        if result.deleted_count:
            return jsonify({
                'success': True,
                'message': 'Site deleted successfully'
            })
        else:
            return jsonify({'error': 'Site not found'}), 404

    except Exception as e:
        print(f"Error deleting site {site_id}: {e}")
        return jsonify({'error': 'Failed to delete site'}), 500


@app.route('/api/stats', methods=['GET'])
def get_stats():
    """Get database statistics"""
    try:
        if collection is None:
            return jsonify({'error': 'Database connection not available'}), 500

        total_sites = collection.count_documents({})
        external_requests = collection.count_documents({'Entry Type': 'external'})

        status_pipeline = [
            {'$group': {'_id': '$Application Status', 'count': {'$sum': 1}}},
            {'$sort': {'count': -1}}
        ]
        status_distribution = list(collection.aggregate(status_pipeline))

        return jsonify({
            'total_sites': total_sites,
            'external_requests': external_requests,
            'status_distribution': status_distribution
        })

    except Exception as e:
        print(f"Error getting stats: {e}")
        return jsonify({'error': 'Failed to retrieve statistics'}), 500


# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"Starting Flask app on port {port}")
    print(f"Debug mode: {debug}")
    print(f"MongoDB URI: {MONGO_URI}")
    print(f"Database: {DATABASE_NAME}")
    print(f"Collection: {COLLECTION_NAME}")

    app.run(host='0.0.0.0', port=port, debug=debug)
