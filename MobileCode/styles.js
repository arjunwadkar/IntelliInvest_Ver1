// MobileCode/styles.js
import { StyleSheet } from 'react-native'

export default StyleSheet.create({
  container: { flex: 1, padding: 16, backgroundColor: '#fff' },
  header: { fontSize: 22, fontWeight: '700', marginBottom: 12 },
  button: { padding: 12, borderRadius: 8, alignItems: 'center', marginRight: 8 },
  primary: { backgroundColor: '#2563eb' },
  accent: { backgroundColor: '#059669' },
  neutral: { backgroundColor: '#6b7280' },
  danger: { backgroundColor: '#ef4444' },
  buttonText: { color: '#fff', fontWeight: '600' },
  chip: { paddingHorizontal: 12, paddingVertical: 8, borderRadius: 20, backgroundColor: '#eee', marginRight: 8 },
  chipActive: { backgroundColor: '#cfe8ff' },
  listItem: { paddingVertical: 12, borderBottomWidth: 1, borderBottomColor: '#f0f0f0' },
  companySymbol: { fontWeight: '700' },
  comparisonContainer: { marginTop: 8, padding: 8, borderRadius: 8, backgroundColor: '#fafafa', borderWidth: 1, borderColor: '#eee' },
  comparisonTitle: { fontWeight: '700', marginBottom: 8 }
})
