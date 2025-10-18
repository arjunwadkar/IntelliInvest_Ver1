// MobileCode/App.jsx
import React, { useEffect, useState, useRef } from 'react'
import { SafeAreaView, View, Text, TouchableOpacity, ActivityIndicator, Alert, Platform } from 'react-native'
import * as FileSystem from 'expo-file-system'
import * as Sharing from 'expo-sharing'
import { captureRef } from 'react-native-view-shot'
import AsyncStorage from '@react-native-async-storage/async-storage'
import Constants from 'expo-constants'
import styles from './styles'
import SectorSelector from './components/SectorSelector'
import CompanyList from './components/CompanyList'
import ComparisonTable from './components/ComparisonTable'
import { fetchSectors, fetchCompanies, analyzeSector } from './api'
import { jsonToCSV } from './utils/csvExport'

const API_BASE = Constants?.manifest?.extra?.API_BASE || ''

export default function App(){
  const [sectorsObj, setSectorsObj] = useState({})
  const [selectedSector, setSelectedSector] = useState('')
  const [selectedSubsector, setSelectedSubsector] = useState('')
  const [companies, setCompanies] = useState([])
  const [selectedMap, setSelectedMap] = useState({})
  const [analysis, setAnalysis] = useState(null)
  const [loading, setLoading] = useState(false)
  const comparisonRef = useRef(null)

  useEffect(()=>{ loadCachedSectors() }, [])

  async function loadCachedSectors(){
    try {
      const cached = await AsyncStorage.getItem('sectors_v1')
      if(cached) setSectorsObj(JSON.parse(cached))
      refreshSectorsFromServer()
    } catch(e){ console.error(e) }
  }

  async function refreshSectorsFromServer(){
    try {
      setLoading(true)
      const data = await fetchSectors(API_BASE)
      setSectorsObj(data)
      await AsyncStorage.setItem('sectors_v1', JSON.stringify(data))
      setLoading(false)
    } catch(e){
      setLoading(false)
      console.error(e)
      Alert.alert('Error', 'Could not fetch sectors from server')
    }
  }

  useEffect(()=> {
    if(selectedSector) fetchCompaniesForSelection()
    else setCompanies([])
  }, [selectedSector, selectedSubsector])

  async function fetchCompaniesForSelection(){
    try {
      setLoading(true)
      const data = await fetchCompanies(API_BASE, selectedSector, selectedSubsector)
      setCompanies(data)
      setLoading(false)
    } catch(e){
      setLoading(false)
      console.error(e)
      Alert.alert('Error', 'Could not fetch companies')
    }
  }

  function toggleSelect(company){
    setSelectedMap(prev => {
      const copy = {...prev}
      if(copy[company.symbol]) delete copy[company.symbol]
      else copy[company.symbol] = company
      return copy
    })
  }

  async function onAnalyze(){
    if(!selectedSector) return Alert.alert('Pick a sector first')
    try {
      setLoading(true)
      const resp = await analyzeSector(API_BASE, selectedSector, selectedSubsector || '', 'real')
      setAnalysis(resp.result || resp)
      setLoading(false)
    } catch(e){
      setLoading(false)
      console.error(e)
      Alert.alert('Error', 'Analysis failed')
    }
  }

  async function onExportCSV(){
    const selected = Object.values(selectedMap)
    if(selected.length === 0) return Alert.alert('Select companies to export')
    const rows = selected.map(c => ({ symbol: c.symbol, name: c.name, market_cap: c.market_cap, sector: c.sector }))
    const csv = jsonToCSV(rows, ['symbol','name','market_cap','sector'])
    const path = `${FileSystem.cacheDirectory}companies_export_${Date.now()}.csv`
    await FileSystem.writeAsStringAsync(path, csv, { encoding: FileSystem.EncodingType.UTF8 })
    if (await Sharing.isAvailableAsync()) {
      await Sharing.shareAsync(path)
    } else {
      Alert.alert('Saved', `Saved to ${path}`)
    }
  }

  async function onCaptureComparison(){
    if(!comparisonRef.current) return Alert.alert('No comparison to capture')
    try {
      const uri = await captureRef(comparisonRef, { format: 'png', quality: 0.9 })
      const dest = `${FileSystem.cacheDirectory}comparison_${Date.now()}.png`
      await FileSystem.copyAsync({ from: uri, to: dest })
      if(await Sharing.isAvailableAsync()){
        await Sharing.shareAsync(dest)
      } else {
        Alert.alert('Saved image', dest)
      }
    } catch(e){
      console.error(e)
      Alert.alert('Error', 'Could not capture image')
    }
  }

  const companiesData = Object.fromEntries(Object.entries(selectedMap).map(([k, v]) => [k, {
    "Market Share": v.market_share ?? v.market_cap ?? '-',
    "Products Manufactured": v.products || v.name || '-',
    "Key Raw Materials": v.raw_materials || '-',
    "Market Cap": v.market_cap || '-'
  }]))

  return (
    <SafeAreaView style={styles.container}>
      <Text style={styles.header}>IntelliInvest</Text>

      <SectorSelector sectorsObj={sectorsObj} selectedSector={selectedSector} setSelectedSector={setSelectedSector} selectedSubsector={selectedSubsector} setSelectedSubsector={setSelectedSubsector} />

      <View style={{flexDirection:'row', marginVertical:8, gap:8}}>
        <TouchableOpacity style={[styles.button, styles.primary]} onPress={fetchCompaniesForSelection}>
          <Text style={styles.buttonText}>Refresh Companies</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.button, styles.accent]} onPress={onAnalyze}>
          <Text style={styles.buttonText}>Analyze</Text>
        </TouchableOpacity>
        <TouchableOpacity style={[styles.button, styles.neutral]} onPress={onExportCSV}>
          <Text style={styles.buttonText}>Export CSV</Text>
        </TouchableOpacity>
      </View>

      {loading && <ActivityIndicator style={{marginVertical:12}} />}

      {analysis && (
        <View style={{marginVertical:8}}>
          <Text style={{fontWeight:'700'}}>Analysis Overview</Text>
          <Text>{typeof analysis.overview === 'string' ? analysis.overview : JSON.stringify(analysis.overview)}</Text>
        </View>
      )}

      <CompanyList companies={companies} selected={selectedMap} toggleSelect={toggleSelect} />

      <View style={{marginTop:12}}>
        <Text style={{fontWeight:'700', marginBottom:8}}>Comparison</Text>
        <ComparisonTable ref={comparisonRef} companiesData={companiesData} />
        <View style={{flexDirection:'row', marginTop:8, gap:8}}>
          <TouchableOpacity style={[styles.button, styles.danger]} onPress={onCaptureComparison}>
            <Text style={styles.buttonText}>Capture Comparison as Image</Text>
          </TouchableOpacity>
        </View>
      </View>

    </SafeAreaView>
  )
}
