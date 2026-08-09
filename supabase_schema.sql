
    -- Create product_keys table
    CREATE TABLE IF NOT EXISTS product_keys (
        id BIGSERIAL PRIMARY KEY,
        product_key VARCHAR(30) UNIQUE NOT NULL,
        key_type VARCHAR(20) NOT NULL CHECK (key_type IN ('scraping_only', 'full_access')),
        is_activated BOOLEAN DEFAULT FALSE,
        machine_id VARCHAR(255),
        machine_name VARCHAR(255),
        activated_at TIMESTAMPTZ,
        expires_at TIMESTAMPTZ,
        created_at TIMESTAMPTZ DEFAULT NOW(),
        updated_at TIMESTAMPTZ DEFAULT NOW()
    );

    -- Create index on product_key for faster lookups
    CREATE INDEX IF NOT EXISTS idx_product_key ON product_keys(product_key);
    
    -- Create index on is_activated for filtering
    CREATE INDEX IF NOT EXISTS idx_is_activated ON product_keys(is_activated);
    
    -- Create function to update updated_at timestamp
    CREATE OR REPLACE FUNCTION update_updated_at_column()
    RETURNS TRIGGER AS $$
    BEGIN
        NEW.updated_at = NOW();
        RETURN NEW;
    END;
    $$ language 'plpgsql';
    
    -- Create trigger to automatically update updated_at
    DROP TRIGGER IF EXISTS update_product_keys_updated_at ON product_keys;
    CREATE TRIGGER update_product_keys_updated_at
        BEFORE UPDATE ON product_keys
        FOR EACH ROW
        EXECUTE FUNCTION update_updated_at_column();
    
    -- Enable Row Level Security (RLS)
    ALTER TABLE product_keys ENABLE ROW LEVEL SECURITY;
    
    -- Create policy to allow service role full access
    DROP POLICY IF EXISTS "Service role has full access" ON product_keys;
    CREATE POLICY "Service role has full access"
        ON product_keys
        FOR ALL
        TO service_role
        USING (true)
        WITH CHECK (true);
    
    -- Create policy for anon/authenticated users to read their own keys
    DROP POLICY IF EXISTS "Users can read product keys" ON product_keys;
    CREATE POLICY "Users can read product keys"
        ON product_keys
        FOR SELECT
        TO anon, authenticated
        USING (true);
    
    -- Create policy for anon/authenticated users to update activation
    DROP POLICY IF EXISTS "Users can activate keys" ON product_keys;
    CREATE POLICY "Users can activate keys"
        ON product_keys
        FOR UPDATE
        TO anon, authenticated
        USING (is_activated = false)
        WITH CHECK (is_activated = true);
    