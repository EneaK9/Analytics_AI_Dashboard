-- Create table for client dashboard configurations
CREATE TABLE IF NOT EXISTS client_dashboard_configs (
    config_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    dashboard_config JSONB NOT NULL,
    is_generated BOOLEAN DEFAULT FALSE,
    generation_timestamp TIMESTAMP WITH TIME ZONE,
    last_updated TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(client_id)
);

-- Create indexes for better performance
CREATE INDEX IF NOT EXISTS idx_dashboard_configs_client_id ON client_dashboard_configs (client_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_configs_generated ON client_dashboard_configs (is_generated);

-- Create dashboard analytics table for tracking metrics
CREATE TABLE IF NOT EXISTS client_dashboard_metrics (
    metric_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    metric_name VARCHAR(255) NOT NULL,
    metric_value JSONB NOT NULL,
    metric_type VARCHAR(100) NOT NULL, -- 'kpi', 'chart_data', 'trend'
    calculated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for metrics table
CREATE INDEX IF NOT EXISTS idx_dashboard_metrics_client_id ON client_dashboard_metrics (client_id);
CREATE INDEX IF NOT EXISTS idx_dashboard_metrics_type ON client_dashboard_metrics (metric_type);
CREATE INDEX IF NOT EXISTS idx_dashboard_metrics_name ON client_dashboard_metrics (client_id, metric_name);

-- Create function to update dashboard config last_updated timestamp
CREATE OR REPLACE FUNCTION update_dashboard_config_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.last_updated = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger to automatically update last_updated
CREATE TRIGGER trigger_update_dashboard_config_timestamp
    BEFORE UPDATE ON client_dashboard_configs
    FOR EACH ROW
    EXECUTE FUNCTION update_dashboard_config_timestamp();

-- Create function to get client dashboard status
CREATE OR REPLACE FUNCTION get_client_dashboard_status(p_client_id UUID)
RETURNS TABLE(
    has_dashboard BOOLEAN,
    is_generated BOOLEAN,
    last_updated TIMESTAMP WITH TIME ZONE,
    metrics_count INTEGER
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        EXISTS(SELECT 1 FROM client_dashboard_configs cdc WHERE cdc.client_id = p_client_id) as has_dashboard,
        COALESCE((SELECT cdc.is_generated FROM client_dashboard_configs cdc WHERE cdc.client_id = p_client_id), FALSE) as is_generated,
        (SELECT cdc.last_updated FROM client_dashboard_configs cdc WHERE cdc.client_id = p_client_id) as last_updated,
        (SELECT COUNT(*)::INTEGER FROM client_dashboard_metrics cdm WHERE cdm.client_id = p_client_id) as metrics_count;
END;
$$ LANGUAGE plpgsql;

-- Create dashboard generation tracking table
CREATE TABLE IF NOT EXISTS client_dashboard_generation (
    generation_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(client_id) ON DELETE CASCADE,
    status VARCHAR(50) NOT NULL DEFAULT 'pending', -- 'pending', 'processing', 'completed', 'failed', 'retrying'
    generation_type VARCHAR(50) NOT NULL DEFAULT 'automatic', -- 'automatic', 'manual'
    attempt_count INTEGER DEFAULT 0,
    max_attempts INTEGER DEFAULT 5,
    last_attempt_at TIMESTAMP WITH TIME ZONE,
    next_retry_at TIMESTAMP WITH TIME ZONE,
    error_type VARCHAR(100), -- 'ai_failure', 'system_error', 'data_error', null for success
    error_message TEXT,
    error_details JSONB,
    started_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    UNIQUE(client_id)
);

-- Create indexes for generation tracking
CREATE INDEX IF NOT EXISTS idx_generation_client_id ON client_dashboard_generation (client_id);
CREATE INDEX IF NOT EXISTS idx_generation_status ON client_dashboard_generation (status);
CREATE INDEX IF NOT EXISTS idx_generation_next_retry ON client_dashboard_generation (next_retry_at);
CREATE INDEX IF NOT EXISTS idx_generation_error_type ON client_dashboard_generation (error_type);

-- Create function to update generation tracking timestamp
CREATE OR REPLACE FUNCTION update_generation_tracking_timestamp()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create trigger for generation tracking
CREATE TRIGGER trigger_update_generation_tracking_timestamp
    BEFORE UPDATE ON client_dashboard_generation
    FOR EACH ROW
    EXECUTE FUNCTION update_generation_tracking_timestamp();

-- Create function to get pending retries
CREATE OR REPLACE FUNCTION get_pending_dashboard_retries()
RETURNS TABLE(
    client_id UUID,
    generation_id UUID,
    attempt_count INTEGER,
    error_type VARCHAR(100),
    next_retry_at TIMESTAMP WITH TIME ZONE
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        g.client_id,
        g.generation_id,
        g.attempt_count,
        g.error_type,
        g.next_retry_at
    FROM client_dashboard_generation g
    WHERE g.status = 'retrying' 
    AND g.next_retry_at <= NOW()
    AND g.attempt_count < g.max_attempts
    ORDER BY g.next_retry_at ASC;
END;
$$ LANGUAGE plpgsql;

-- Create function to calculate next retry time with exponential backoff
CREATE OR REPLACE FUNCTION calculate_next_retry_time(attempt_count INTEGER)
RETURNS TIMESTAMP WITH TIME ZONE AS $$
DECLARE
    base_delay INTEGER := 60; -- 1 minute base delay
    max_delay INTEGER := 1800; -- 30 minutes max delay
    delay_seconds INTEGER;
BEGIN
    -- Exponential backoff: 1min, 5min, 15min, 30min, 30min...
    CASE attempt_count
        WHEN 1 THEN delay_seconds := 60;     -- 1 minute
        WHEN 2 THEN delay_seconds := 300;    -- 5 minutes  
        WHEN 3 THEN delay_seconds := 900;    -- 15 minutes
        ELSE delay_seconds := 1800;          -- 30 minutes
    END CASE;
    
    RETURN NOW() + (delay_seconds || ' seconds')::INTERVAL;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE client_dashboard_configs IS 'Stores personalized dashboard configurations for each client';
COMMENT ON COLUMN client_dashboard_configs.dashboard_config IS 'JSON configuration including widgets, charts, KPIs, and layout';
COMMENT ON COLUMN client_dashboard_configs.is_generated IS 'Flag indicating if dashboard was AI-generated';
COMMENT ON COLUMN client_dashboard_configs.generation_timestamp IS 'When the dashboard was initially generated by AI';

COMMENT ON TABLE client_dashboard_metrics IS 'Stores calculated metrics and chart data for client dashboards';
COMMENT ON COLUMN client_dashboard_metrics.metric_value IS 'JSON data containing the calculated metric value and metadata';
COMMENT ON COLUMN client_dashboard_metrics.metric_type IS 'Type of metric: kpi, chart_data, or trend';

COMMENT ON TABLE client_dashboard_generation IS 'Tracks dashboard generation attempts and retry logic';
COMMENT ON COLUMN client_dashboard_generation.status IS 'Current generation status: pending, processing, completed, failed, retrying';
COMMENT ON COLUMN client_dashboard_generation.error_type IS 'Type of error: ai_failure (retryable), system_error, data_error (non-retryable)';
COMMENT ON COLUMN client_dashboard_generation.attempt_count IS 'Number of generation attempts made';
COMMENT ON COLUMN client_dashboard_generation.next_retry_at IS 'When to attempt next retry (for retrying status)'; 