"""Tests for MCP server API base configuration and normalization."""

import pytest
import json
import ast
from retrorecon.mcp.config import MCPConfig
from retrorecon.mcp.server import RetroReconMCPServer


class TestAPIBaseNormalization:
    """Test that alt_api_bases is properly normalized in various scenarios."""
    
    def test_normalize_alt_api_bases_list(self):
        """Test normalization of normal list input."""
        config = MCPConfig()
        server = RetroReconMCPServer(config=config)
        
        alt_api_bases = ["http://192.168.1.98:1234/v1", "http://backup.com/v1"]
        result = server._normalize_alt_api_bases(alt_api_bases)
        
        assert result == ["http://192.168.1.98:1234/v1", "http://backup.com/v1"]
        
    def test_normalize_alt_api_bases_string_repr(self):
        """Test normalization of string representation of list."""
        config = MCPConfig()
        server = RetroReconMCPServer(config=config)
        
        # This is the original bug scenario - string repr of list
        alt_api_bases = "['http://192.168.1.98:1234/v1']"
        result = server._normalize_alt_api_bases(alt_api_bases)
        
        assert result == ["http://192.168.1.98:1234/v1"]
        
    def test_normalize_alt_api_bases_json_string(self):
        """Test normalization of JSON string."""
        config = MCPConfig()
        server = RetroReconMCPServer(config=config)
        
        alt_api_bases = '["http://192.168.1.98:1234/v1", "http://backup.com/v1"]'
        result = server._normalize_alt_api_bases(alt_api_bases)
        
        assert result == ["http://192.168.1.98:1234/v1", "http://backup.com/v1"]
        
    def test_normalize_alt_api_bases_empty_list(self):
        """Test normalization of empty list."""
        config = MCPConfig()
        server = RetroReconMCPServer(config=config)
        
        alt_api_bases = []
        result = server._normalize_alt_api_bases(alt_api_bases)
        
        assert result == []
        
    def test_normalize_alt_api_bases_none(self):
        """Test normalization of None."""
        config = MCPConfig()
        server = RetroReconMCPServer(config=config)
        
        alt_api_bases = None
        result = server._normalize_alt_api_bases(alt_api_bases)
        
        assert result == []
        
    def test_normalize_alt_api_bases_single_string(self):
        """Test normalization of single string."""
        config = MCPConfig()
        server = RetroReconMCPServer(config=config)
        
        alt_api_bases = "http://192.168.1.98:1234/v1"
        result = server._normalize_alt_api_bases(alt_api_bases)
        
        assert result == ["http://192.168.1.98:1234/v1"]
        
    def test_api_bases_construction_with_string_repr(self):
        """Test that API bases are constructed correctly with string representation."""
        config = MCPConfig()
        config.api_base = "http://127.0.0.1:3000/sse"
        config.alt_api_bases = "['http://192.168.1.98:1234/v1']"  # Bug scenario
        
        server = RetroReconMCPServer(config=config)
        
        # Simulate what happens in _llm_chat
        normalized_alt_bases = server._normalize_alt_api_bases(config.alt_api_bases)
        api_bases = [config.api_base] + normalized_alt_bases
        
        assert api_bases == ["http://127.0.0.1:3000/sse", "http://192.168.1.98:1234/v1"]
        
        # Test that URL construction works correctly
        url = f"{api_bases[1]}/chat/completions"
        assert url == "http://192.168.1.98:1234/v1/chat/completions"
        assert not url.startswith("http://[")  # This would indicate the bug
        
    def test_api_bases_construction_prevents_character_expansion(self):
        """Test that the fix prevents character-by-character expansion."""
        config = MCPConfig()
        config.api_base = "http://127.0.0.1:3000/sse"
        config.alt_api_bases = "['http://192.168.1.98:1234/v1']"  # Bug scenario
        
        server = RetroReconMCPServer(config=config)
        
        # Before the fix, this would have resulted in character-by-character expansion
        # Now it should work correctly
        normalized_alt_bases = server._normalize_alt_api_bases(config.alt_api_bases)
        api_bases = [config.api_base] + normalized_alt_bases
        
        # Should not expand to individual characters
        assert len(api_bases) == 2
        assert api_bases[1] == "http://192.168.1.98:1234/v1"
        
        # Should not contain individual characters like '[', "'", 'h', 't', etc.
        assert "[" not in api_bases[1]
        assert "'" not in api_bases[1]