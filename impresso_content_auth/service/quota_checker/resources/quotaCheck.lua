-- KEYS[1] = user:{user_id}:bloom
-- KEYS[2] = user:{user_id}:count
-- KEYS[3] = user:{user_id}:first_access
-- ARGV[1] = doc_id
-- ARGV[2] = quota_limit (200000)
-- ARGV[3] = current_timestamp
-- ARGV[4] = window_seconds (2592000 = 30 days)

--- Bloom filter based quota checker
--- 
--- This script tracks unique document accesses per user within a rolling time window.
--- It uses a probabilistic bloom filter for memory-efficient "seen document" checking.
--- 
--- Quota check requirements:
--- - Allow up to N unique document accesses per user per time window
--- - Time window resets after expiry (e.g. 30 days from first access in current window)
--- - When under quota: allow access to any document (both new and previously seen)
--- - For new documents: increment the quota counter
--- - For previously seen documents: allow access WITHOUT incrementing the counter
--- - Bloom filter false positives (~0.1%): acceptable to treat as "seen" (no counter increment)
--- - When at quota: deny access to NEW documents only. Previously seen documents always allowed.
---   Note: Due to bloom filter false positives, ~0.1% of truly new documents may be incorrectly
---   allowed when at quota (they'll be treated as "seen"). This is an acceptable trade-off.

local bloom_key = KEYS[1]
local count_key = KEYS[2]
local first_access_key = KEYS[3]
local doc_id = ARGV[1]
local quota_limit = tonumber(ARGV[2])
local current_time = tonumber(ARGV[3])
local window_seconds = tonumber(ARGV[4])

-- Error rate values (https://redis.io/docs/latest/develop/data-types/probabilistic/bloom-filter/):
--
-- 0.0001 = 0.01% false positive rate (1 in 10,000) - ~468 KB per 200K items
-- 0.001 = 0.1% false positive rate (1 in 1000) - ~351 KB per 200K items
-- 0.01  = 1% false positive rate (1 in 100) - ~234 KB per 200K items
--
local fp_rate = 0.0001

-- Helper function to initialize a new quota window
local function init_quota_window(start_time)
    redis.call('SET', first_access_key, start_time)
    redis.call('EXPIRE', first_access_key, math.ceil(window_seconds))
    
    -- Create bloom filter with predefined error rate and capacity for quota_limit items
    redis.call('DEL', bloom_key)  -- Clean up old bloom filter before recreating
    redis.call('BF.RESERVE', bloom_key, fp_rate, quota_limit)
    redis.call('EXPIRE', bloom_key, math.ceil(window_seconds))
    
    -- Add the first document to the bloom filter and initialize counter
    redis.call('BF.ADD', bloom_key, doc_id)
    redis.call('SET', count_key, 1)
    redis.call('EXPIRE', count_key, math.ceil(window_seconds))
    
    return {1, 1, 1, start_time, window_seconds}  -- allowed, count=1, was_counted=1, window_start, seconds_until_reset
end

-- Check if this is the user's first access ever, or if the window has expired (key was deleted by TTL)
local first_access_timestamp = redis.call('GET', first_access_key)

if not first_access_timestamp then
    -- First access ever for this user, or window expired and keys were auto-deleted
    -- Initialize a new quota window
    return init_quota_window(current_time)
end

-- Safety check: manually verify if window has expired
-- (This shouldn't happen since Redis TTL should auto-delete keys, but guards against clock skew)
first_access_timestamp = tonumber(first_access_timestamp)
local window_age = current_time - first_access_timestamp

if window_age >= window_seconds then
    -- Window has expired - reset everything and start a fresh window
    return init_quota_window(current_time)
end

-- Within active window - check if document was previously accessed
local exists = redis.call('BF.EXISTS', bloom_key, doc_id)  -- 1 = probably seen, 0 = definitely new
local count = tonumber(redis.call('GET', count_key) or 0)  -- Current unique document count
local at_quota = count >= quota_limit  -- Whether user has reached their quota limit
local remaining_window = window_seconds - window_age  -- Seconds until window resets

if exists == 1 then
    -- Bloom filter indicates document was probably seen before (~99%, ~99.9% or ~99.99% accuracy - depends on fp_rate setting)
    -- Allow access without incrementing counter (even if at quota)
    -- Note: FP rate means some truly new docs will be treated as "seen" (rate depends on fp_rate setting)
    return {1, count, 0, first_access_timestamp, remaining_window}  
    -- allowed=1, count, was_counted=0, window_start, seconds_until_reset
end

----------------------------------------------------------------------
-- If we reach here, bloom filter confirms document is definitely new
-- (Bloom filters have no false negatives - if it says "not seen", it's 100% true)
----------------------------------------------------------------------

-- User has reached quota limit - deny access to this new document
if at_quota then
    return {0, count, 0, first_access_timestamp, remaining_window}  
    -- allowed=0 (denied), count, was_counted=0, window_start, seconds_until_reset
end

-- User is under quota - allow access and track this new document

-- Add document to bloom filter (for future "seen" checks)
redis.call('BF.ADD', bloom_key, doc_id)
-- Increment the unique document counter
local new_count = redis.call('INCR', count_key)

-- Ensure counter has TTL set (defensive: should already have TTL from initialization)
local ttl = redis.call('TTL', count_key)
if ttl == -1 then  -- -1 means no expiration set
    redis.call('EXPIRE', count_key, math.ceil(remaining_window))
end

return {1, new_count, 1, first_access_timestamp, remaining_window}  
-- allowed=1, new_count, was_counted=1, window_start, seconds_until_reset