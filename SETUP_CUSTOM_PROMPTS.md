# Custom Prompt Templates Setup

The custom prompt template feature requires creating a database table in Supabase. Follow these steps to enable it:

## 🎯 **Quick Setup (Recommended)**

### **Step 1: Access Supabase Dashboard**
1. Go to [supabase.com](https://supabase.com)
2. Sign in to your account
3. Select your project: `rancheye-01`

### **Step 2: Open SQL Editor**
1. In the left sidebar, click **"SQL Editor"**
2. Click **"New Query"**

### **Step 3: Run the Setup SQL**
1. Copy the contents of `database/custom_prompt_templates.sql`
2. Paste it into the SQL Editor
3. Click **"Run"** (or press Ctrl/Cmd + Enter)

### **Step 4: Verify Setup**
1. Go to **"Table Editor"** in the sidebar
2. You should see a new table: `custom_prompt_templates`
3. The table should have default system templates pre-loaded

## 🔧 **Manual Setup (Alternative)**

If the SQL file doesn't work, create the table manually:

```sql
CREATE TABLE custom_prompt_templates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    prompt_text TEXT NOT NULL,
    analysis_type TEXT NOT NULL,
    is_default BOOLEAN DEFAULT FALSE,
    is_system BOOLEAN DEFAULT FALSE,
    created_by TEXT DEFAULT 'web_user',
    usage_count INTEGER DEFAULT 0,
    last_used_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);
```

## ✅ **Verification**

After setup, the custom prompt feature should work:

1. **Go to the AI Image Analysis section**
2. **Expand "Advanced Options"**
3. **Modify a prompt and click "💾 Save Prompt"**
4. **You should see the save modal instead of an error**

## 🚨 **Troubleshooting**

### **Error: "failed to save prompt template"**
- The table hasn't been created yet
- Run the SQL setup steps above

### **Error: "relation custom_prompt_templates does not exist"**
- Same as above - table needs to be created

### **Error: "permission denied"**
- Make sure you're using the Service Role Key in your environment variables
- Check that `SUPABASE_SERVICE_ROLE_KEY` is set correctly

### **No custom templates appearing in dropdown**
- Table exists but may be empty
- Try saving a template first
- Check browser console for loading errors

## 🎉 **Success Indicators**

You'll know it's working when:
- ✅ Save prompt button appears when editing prompts
- ✅ Save modal opens without errors
- ✅ Success toast appears after saving
- ✅ Custom templates appear in Analysis Type dropdown with 📝 icon
- ✅ Templates auto-load when selected

## 📁 **Files Involved**

- `database/custom_prompt_templates.sql` - Full table schema
- `SETUP_CUSTOM_PROMPTS.md` - This setup guide
- `PROMPT_TEMPLATES_GUIDE.md` - User guide for the feature

Once setup is complete, refer to the **PROMPT_TEMPLATES_GUIDE.md** for how to use the feature!