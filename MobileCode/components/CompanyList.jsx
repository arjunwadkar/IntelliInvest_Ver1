// MobileCode/components/CompanyList.jsx
import React from 'react'
import { View, Text, TouchableOpacity, FlatList } from 'react-native'
import styles from '../styles'

export default function CompanyList({ companies = [], selected = {}, toggleSelect }){
  const renderItem = ({ item }) => {
    const isSelected = !!selected[item.symbol]
    return (
      <TouchableOpacity onPress={()=>toggleSelect(item)} style={styles.listItem}>
        <View style={{flexDirection:'row', justifyContent:'space-between', alignItems:'center'}}>
          <View>
            <Text style={styles.companySymbol}>{item.symbol}</Text>
            <Text>{item.name}</Text>
          </View>
          <View style={{alignItems:'flex-end'}}>
            <Text>{item.market_cap ?? '-'}</Text>
            <Text>{isSelected ? '✓ Selected' : 'Tap'}</Text>
          </View>
        </View>
      </TouchableOpacity>
    )
  }

  return <FlatList data={companies} keyExtractor={(i)=>i.symbol || i.name} renderItem={renderItem} />
}
