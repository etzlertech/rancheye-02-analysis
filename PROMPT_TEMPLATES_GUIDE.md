# Custom Prompt Templates Guide

The RanchEye AI Analysis system now supports saving and managing custom prompt templates, allowing you to refine and reuse your analysis prompts.

## 🎯 **Features**

### ✅ **Save Prompt Templates**
- **Save as Default**: Update the default prompt for any analysis type
- **Save as Copy**: Create named custom templates that appear in the dropdown
- **Auto-population**: Custom prompts automatically load when selected

### ✅ **Template Management**
- **Usage Tracking**: Tracks how often templates are used
- **Version Control**: Update existing templates or create new versions
- **Categories**: Templates organized by analysis type

### ✅ **Smart Integration**
- **Auto-expand**: Selecting a custom template automatically opens Advanced Options
- **Current Template Indicator**: Shows which template is currently being used
- **Seamless Workflow**: Templates integrate with multi-model analysis

## 🔧 **How to Use**

### **1. Creating a Custom Template**

1. **Modify an existing prompt** in the Advanced Options textarea
2. **Click the "💾 Save Prompt" button** (appears when prompt is not empty)
3. **Choose save option**:
   - ✅ **Save as default**: Replaces the system default for that analysis type
   - ❌ **Save as copy**: Creates a new named template

### **2. Save as Default**
```
☑️ Save as default for Gate Detection
```
- Updates the default prompt for that analysis type
- All future analyses of that type will use your custom prompt
- Can be reverted by system admins if needed

### **3. Save as Copy**
```
Template Name: "Enhanced Gate Detection with Confidence Thresholds"
Description: "More detailed gate analysis with specific confidence requirements"
```
- Creates a new template accessible from the Analysis Type dropdown
- Appears with a 📝 icon: `📝 Enhanced Gate Detection with Confidence Thresholds`
- Can be selected for any future analysis

### **4. Using Saved Templates**

Custom templates appear in the **Analysis Type dropdown**:
```
Gate Detection
Door Detection  
Water Level
Feed Bin Status
Animal Detection
📝 Enhanced Gate Detection with Confidence Thresholds  ← Your saved template
📝 Detailed Water Assessment
📝 Custom Livestock Behavior Analysis
Custom Analysis
```

## 🗄️ **Database Schema**

### **custom_prompt_templates Table**
```sql
- id: UUID (primary key)
- name: Template name
- description: Optional description
- prompt_text: The actual prompt content
- analysis_type: 'gate_detection', 'door_detection', etc.
- is_default: Whether this replaces the system default
- is_system: System vs user-created templates
- usage_count: How many times it's been used
- last_used_at: When it was last used
- created_at, updated_at: Timestamps
```

## 🔌 **API Endpoints**

### **Get Templates**
```
GET /api/prompt-templates
GET /api/prompt-templates?analysis_type=gate_detection
```

### **Save Template**
```
POST /api/prompt-templates
{
  "name": "Enhanced Gate Analysis",
  "description": "More detailed gate detection",
  "prompt_text": "Your custom prompt...",
  "analysis_type": "gate_detection",
  "save_as_default": false
}
```

### **Update Template**
```
PUT /api/prompt-templates/{id}
```

### **Delete Template**
```
DELETE /api/prompt-templates/{id}
```

### **Set as Default**
```
POST /api/prompt-templates/{id}/set-default
```

### **Track Usage**
```
POST /api/prompt-templates/{id}/increment-usage
```

## 💡 **Use Cases**

### **1. Specialized Ranch Setups**
```
Template: "Feedlot Gate Detection"
Analysis Type: Gate Detection
Prompt: Custom prompt optimized for feedlot environments with specific gate types
```

### **2. Seasonal Adjustments**
```
Template: "Winter Water Analysis"  
Analysis Type: Water Level
Prompt: Accounts for ice, snow, and winter-specific water level indicators
```

### **3. Multi-Species Ranches**
```
Template: "Mixed Livestock Detection"
Analysis Type: Animal Detection  
Prompt: Enhanced to distinguish between cattle, horses, sheep, etc.
```

### **4. Equipment-Specific Analysis**
```
Template: "Red Brand Gate Analysis"
Analysis Type: Gate Detection
Prompt: Optimized for specific gate hardware and mechanisms
```

## 🎛️ **Advanced Features**

### **Template Inheritance**
- **System defaults** can be overridden by **custom defaults**
- **Custom defaults** apply to all analyses of that type
- **Specific templates** can be selected for individual analyses

### **Usage Analytics**
- Track which templates are most effective
- Identify popular custom prompts
- Monitor template performance over time

### **Template Sharing** (Future Feature)
- Export templates for sharing between ranch setups
- Import community-created templates
- Version control for collaborative prompt development

## 🔒 **Permissions & Safety**

### **Template Constraints**
- Cannot delete system default templates
- Custom defaults can be reverted by admins
- User templates are isolated by creator

### **Data Integrity**
- Templates validated before saving
- Automatic backup of system defaults
- Usage tracking for audit trails

## 🚀 **Example Workflow**

1. **Start with default**: Use "Gate Detection" analysis type
2. **Customize prompt**: Modify the prompt in Advanced Options to better suit your specific gate type
3. **Test analysis**: Run the analysis to verify the prompt works well
4. **Save template**: Click "💾 Save Prompt" and save as "Ranch Main Gate Analysis"
5. **Future use**: Select "📝 Ranch Main Gate Analysis" from the dropdown for consistent results
6. **Iterate**: Continue refining and saving new versions as needed

This system allows you to build a library of specialized prompts tailored to your specific ranch environment and analysis needs!