/**
 * Settings API Service
 * Educational Note: Handles all API key management operations with the backend.
 * This service provides methods for CRUD operations on API keys stored in .env.
 */

import axios from 'axios';

const API_BASE_URL = 'http://localhost:5000/api/v1';

export interface ApiKey {
  id: string;
  name: string;
  description: string;
  category: 'ai' | 'storage' | 'utility';
  required?: boolean;
  value: string;
  is_set: boolean;
}

export interface ApiKeyUpdate {
  id: string;
  value: string;
}

export interface ValidationResult {
  valid: boolean;
  message: string;
}

class SettingsAPI {
  /**
   * Get all API keys from the backend
   * Educational Note: Returns masked values for security
   */
  async getApiKeys(): Promise<ApiKey[]> {
    try {
      const response = await axios.get(`${API_BASE_URL}/settings/api-keys`);
      return response.data.api_keys;
    } catch (error) {
      console.error('Error fetching API keys:', error);
      throw error;
    }
  }

  /**
   * Update multiple API keys
   * Educational Note: This triggers a backend .env update and potential Flask reload
   */
  async updateApiKeys(apiKeys: ApiKeyUpdate[]): Promise<void> {
    try {
      await axios.post(`${API_BASE_URL}/settings/api-keys`, {
        api_keys: apiKeys
      });
    } catch (error) {
      console.error('Error updating API keys:', error);
      throw error;
    }
  }

  /**
   * Delete a specific API key
   * Educational Note: Removes the key from .env file
   */
  async deleteApiKey(keyId: string): Promise<void> {
    try {
      await axios.delete(`${API_BASE_URL}/settings/api-keys/${keyId}`);
    } catch (error) {
      console.error('Error deleting API key:', error);
      throw error;
    }
  }

  /**
   * Validate an API key
   * Educational Note: Tests if an API key works by making a test request
   */
  async validateApiKey(keyId: string, value: string): Promise<ValidationResult> {
    try {
      const response = await axios.post(`${API_BASE_URL}/settings/api-keys/validate`, {
        key_id: keyId,
        value: value
      });
      return {
        valid: response.data.valid,
        message: response.data.message
      };
    } catch (error) {
      console.error('Error validating API key:', error);
      return {
        valid: false,
        message: 'Validation failed'
      };
    }
  }
}

export const settingsAPI = new SettingsAPI();

// ============================================================================
// Processing Settings Types and API
// ============================================================================

export interface TierConfig {
  name: string;
  description: string;
  max_workers: number;
  pages_per_minute: number;
}

export interface AvailableTier extends TierConfig {
  tier: number;
}

export interface ProcessingSettings {
  anthropic_tier: number;
  tier_config: TierConfig;
}

class ProcessingSettingsAPI {
  /**
   * Get current processing settings
   * Educational Note: Returns the current tier configuration for parallel processing
   */
  async getSettings(): Promise<{ settings: ProcessingSettings; available_tiers: AvailableTier[] }> {
    try {
      const response = await axios.get(`${API_BASE_URL}/settings/processing`);
      return {
        settings: response.data.settings,
        available_tiers: response.data.available_tiers,
      };
    } catch (error) {
      console.error('Error fetching processing settings:', error);
      throw error;
    }
  }

  /**
   * Update processing settings
   * Educational Note: Saves the selected tier to .env file
   */
  async updateSettings(settings: { anthropic_tier: number }): Promise<ProcessingSettings> {
    try {
      const response = await axios.post(`${API_BASE_URL}/settings/processing`, settings);
      return response.data.settings;
    } catch (error) {
      console.error('Error updating processing settings:', error);
      throw error;
    }
  }
}

export const processingSettingsAPI = new ProcessingSettingsAPI();