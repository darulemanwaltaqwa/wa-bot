import json

# Read the file
with open('whatsapp_interactive_menus.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# Add social media links to Urdu opt_1
urdu_social = "\n\n🌐 *ہمیں سوشل میڈیا پر فالو کریں*\n- **فیس بک:** https://www.facebook.com/darulemanwaltaqwa/\n- **یوٹیوب:** https://www.youtube.com/@darulemanwaltaqwa\n- **ٹویٹر/ایکس:** @daruleman_off"
data['responses_data']['opt_1']['urdu'] = data['responses_data']['opt_1']['urdu'].replace('✨ رابطے میں رہیں', '🌐 *ہمیں سوشل میڈیا پر فالو کریں*\n- **فیس بک:** https://www.facebook.com/darulemanwaltaqwa/\n- **یوٹیوب:** https://www.youtube.com/@darulemanwaltaqwa\n- **ٹویٹر/ایکس:** @daruleman_off\n\n✨ رابطے میں رہیں')

# Add social media links to Pashto opt_1
pashto_social = "\n\n🌐 *زموږ د سوشل میډیا پر تعقیب کړئ*\n- **فیس بک:** https://www.facebook.com/darulemanwaltaqwa/\n- **یوټیوب:** https://www.youtube.com/@darulemanwaltaqwa\n- **ټویٹر/ایکس:** @daruleman_off"
data['responses_data']['opt_1']['pashto'] = data['responses_data']['opt_1']['pashto'].replace('✨ په اړیکه کې اوسئ', '🌐 *زموږ د سوشل میډیا پر تعقیب کړئ*\n- **فیس بک:** https://www.facebook.com/darulemanwaltaqwa/\n- **یوټیوب:** https://www.youtube.com/@darulemanwaltaqwa\n- **ټویٹر/ایکس:** @daruleman_off\n\n✨ په اړیکه کې اوسئ')

# Write back
with open('whatsapp_interactive_menus.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ Social media links added to Urdu and Pashto opt_1 responses\!")
