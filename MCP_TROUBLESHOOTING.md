# MCP Troubleshooting Guide

## Common MCP Connection Issues

### 1. MCP Not Available in Claude Code (VS Code/Cursor)

**Symptom**: Claude in your code editor says it can't access database or browser
**Reason**: MCP is ONLY available in Claude Desktop app
**Solution**: Use Claude Desktop for MCP operations

### 2. MCP Not Showing in Claude Desktop

**Symptom**: No MCP icon or "No MCP servers connected"
**Solutions**:

1. **Check Config File Syntax**
   ```bash
   # Validate JSON syntax
   python -m json.tool ~/Library/Application\ Support/Claude/claude_desktop_config.json
   ```

2. **Verify Config Location**
   ```bash
   # macOS
   ls -la ~/Library/Application\ Support/Claude/claude_desktop_config.json
   
   # Windows
   # %APPDATA%\Claude\claude_desktop_config.json
   
   # Linux
   # ~/.config/Claude/claude_desktop_config.json
   ```

3. **Check for Multiple Clauds**
   - Quit ALL Claude instances
   - Check Activity Monitor/Task Manager
   - Restart only Claude Desktop (not VS Code extension)

### 3. Supabase MCP Not Working

**Symptom**: "Cannot connect to Supabase" in Claude Desktop
**Solutions**:

1. **Verify Environment Variables**
   ```json
   {
     "mcpServers": {
       "supabase": {
         "command": "npx",
         "args": ["-y", "@modelcontextprotocol/server-supabase", "postgres://..."]
       }
     }
   }
   ```

2. **Check Connection String**
   - Must include full PostgreSQL connection string
   - Format: `postgres://[user]:[password]@[host]:[port]/[database]`
   - Get from Supabase Dashboard > Settings > Database

3. **Test Connection Outside Claude**
   ```bash
   # Test with psql
   psql "postgres://..."
   ```

### 4. Puppeteer MCP Not Launching Browser

**Symptom**: Browser window doesn't appear
**Solutions**:

1. **Check Headless Setting**
   ```json
   "env": {
     "PUPPETEER_LAUNCH_OPTIONS": "{ \"headless\": false }"
   }
   ```

2. **Install Chrome**
   - Puppeteer needs Chrome or Chromium
   - On macOS: `brew install google-chrome`

3. **Check Permissions**
   - macOS: System Preferences > Security & Privacy
   - May need to allow Chrome automation

### 5. Both MCP Servers Conflict

**Symptom**: One MCP works but not the other
**Solution**: Ensure unique names and no port conflicts

```json
{
  "mcpServers": {
    "supabase": {
      // Supabase config
    },
    "puppeteer": {
      // Puppeteer config
    }
  }
}
```

### 6. MCP Commands Not Recognized

**Symptom**: Claude doesn't understand "Navigate to..." or database queries
**Solutions**:

1. **Check MCP Icon**: Must show connected servers
2. **Use Correct Syntax**: Natural language, not code
3. **Restart Claude Desktop**: Full quit and restart

## Quick Diagnostic Steps

### 1. Test MCP Connection
```
In Claude Desktop:
"Show me the list of tables in the database"

If this fails, Supabase MCP isn't connected
```

### 2. Test Puppeteer
```
In Claude Desktop:
"Navigate to https://google.com"

If browser doesn't open, Puppeteer MCP isn't working
```

### 3. Check Claude Desktop Logs

**macOS**:
```bash
tail -f ~/Library/Logs/Claude/mcp*.log
```

**Windows**:
```
%APPDATA%\Claude\Logs\
```

### 4. Verify Node.js
```bash
node --version  # Must be installed
npm --version   # Must be installed
npx --version   # Must be available
```

## Environment-Specific Issues

### macOS Specific
- Check Gatekeeper: `xattr -d com.apple.quarantine /Applications/Claude.app`
- Grant accessibility permissions
- Check ~/.zshrc or ~/.bash_profile for PATH

### Windows Specific
- Run as Administrator if needed
- Check Windows Defender exclusions
- Verify npm is in system PATH

### Linux Specific
- Check AppImage permissions: `chmod +x Claude.AppImage`
- May need to install additional dependencies

## Reset and Reinstall

### Nuclear Option - Full Reset

1. **Backup Config**
   ```bash
   cp ~/Library/Application\ Support/Claude/claude_desktop_config.json ~/Desktop/
   ```

2. **Clear Claude Data**
   ```bash
   rm -rf ~/Library/Application\ Support/Claude/
   rm -rf ~/Library/Caches/Claude/
   ```

3. **Reinstall Claude Desktop**
   - Download fresh from anthropic.com
   - Start with minimal config
   - Add MCP servers one at a time

### Test with Minimal Config

Start with just one MCP server:

```json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@modelcontextprotocol/server-puppeteer"]
    }
  }
}
```

Then add others once working.

## Getting Help

### Information to Provide

When asking for help, include:

1. **Claude Desktop Version**: Help > About
2. **OS Version**: macOS/Windows/Linux version
3. **Config File**: (sanitize passwords)
4. **Error Messages**: Screenshots or exact text
5. **What You've Tried**: List troubleshooting steps

### Where to Get Help

1. **Anthropic Support**: support.anthropic.com
2. **MCP GitHub**: github.com/modelcontextprotocol
3. **Community Forums**: Discord/Reddit Claude communities

## Pro Tips

1. **Always Restart Fully**: Cmd+Q, not just close window
2. **One Change at a Time**: Test after each config edit
3. **Keep Backups**: Save working configs
4. **Use Desktop for MCP**: Don't expect it in VS Code
5. **Check Logs First**: Often reveals the issue

Remember: MCP is a Claude Desktop exclusive feature!