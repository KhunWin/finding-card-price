-- Migration script to increase product_key column length
-- Run this in Supabase SQL Editor

-- Alter the product_key column to allow longer keys
ALTER TABLE product_keys 
ALTER COLUMN product_key TYPE VARCHAR(50);

-- Verify the change
SELECT column_name, data_type, character_maximum_length 
FROM information_schema.columns 
WHERE table_name = 'product_keys' 
AND column_name = 'product_key';
