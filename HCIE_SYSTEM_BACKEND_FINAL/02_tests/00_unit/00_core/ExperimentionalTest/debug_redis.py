import redis
import json

def debug_redis():
    """Debug Redis to see what's actually stored"""
    try:
        # Connect to Redis
        r = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
        
        # Check all keys
        print("=== All Redis Keys ===")
        keys = r.keys('*')
        for key in sorted(keys):
            print(f"Key: {key}")
            
            # Check if it's a hash
            if r.type(key) == 'hash':
                hash_data = r.hgetall(key)
                for field, value in hash_data.items():
                    print(f"  {field}: {value}")
            else:
                value = r.get(key)
                print(f"  Value: {value}")
            print()
        
        # Test a fresh user
        print("=== Testing Fresh User ===")
        user_id = "debug_test_user"
        concept_id = "ct_abstraction"
        
        # Check mastery key
        mastery_key = f"user:{user_id}:mastery"
        print(f"Mastery key: {mastery_key}")
        
        if r.exists(mastery_key):
            alpha = float(r.hget(mastery_key, f"{concept_id}:alpha") or 0)
            beta = float(r.hget(mastery_key, f"{concept_id}:beta") or 0)
            mastery = alpha / (alpha + beta) if (alpha + beta) > 0 else 0
            print(f"Alpha: {alpha}, Beta: {beta}, Mastery: {mastery}")
        else:
            print("Key does not exist")
            
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    debug_redis()
