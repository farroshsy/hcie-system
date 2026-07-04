// HCIE Tutor — Expo shell over the shared web interface (WebView).
// Honesty contract (== thesis §3.2.4 wording): this client "menghadirkan antarmuka
// tutor pada perangkat seluler menggunakan API yang sama" — it is a cross-platform
// shell over the same gateway, NOT a from-scratch native UI (that is future work).
import { useRef, useState, useCallback } from 'react'
import {
  SafeAreaView, View, Text, ActivityIndicator, TouchableOpacity,
  StyleSheet, BackHandler, Platform, RefreshControl, ScrollView,
} from 'react-native'
import { StatusBar } from 'expo-status-bar'
import { WebView } from 'react-native-webview'
import Constants from 'expo-constants'
import { useEffect } from 'react'

const TUTOR_URL =
  Constants.expoConfig?.extra?.tutorUrl ?? 'https://farrospc.tailb58de0.ts.net/'

const NAVY = '#172F57'

export default function App() {
  const web = useRef(null)
  const [loading, setLoading] = useState(true)
  const [failed, setFailed] = useState(false)
  const [canGoBack, setCanGoBack] = useState(false)

  // Android hardware back → WebView history back
  useEffect(() => {
    if (Platform.OS !== 'android') return
    const sub = BackHandler.addEventListener('hardwareBackPress', () => {
      if (canGoBack && web.current) { web.current.goBack(); return true }
      return false
    })
    return () => sub.remove()
  }, [canGoBack])

  const reload = useCallback(() => {
    setFailed(false)
    setLoading(true)
    web.current?.reload()
  }, [])

  if (failed) {
    return (
      <SafeAreaView style={[styles.fill, { backgroundColor: NAVY }]}>
        <StatusBar style="light" />
        <ScrollView
          contentContainerStyle={styles.center}
          refreshControl={<RefreshControl refreshing={false} onRefresh={reload} tintColor="#fff" />}
        >
          <Text style={styles.errTitle}>Tidak dapat terhubung</Text>
          <Text style={styles.errBody}>
            Server tutor tidak terjangkau. Pastikan perangkat terhubung internet dan
            server HCIE berjalan, lalu coba lagi.
          </Text>
          <TouchableOpacity style={styles.retryBtn} onPress={reload}>
            <Text style={styles.retryTxt}>Coba lagi</Text>
          </TouchableOpacity>
          <Text style={styles.errUrl}>{TUTOR_URL}</Text>
        </ScrollView>
      </SafeAreaView>
    )
  }

  return (
    <SafeAreaView style={[styles.fill, { backgroundColor: NAVY }]}>
      <StatusBar style="light" />
      <WebView
        ref={web}
        source={{ uri: TUTOR_URL }}
        style={styles.fill}
        onLoadStart={() => setLoading(true)}
        onLoadEnd={() => setLoading(false)}
        onError={() => { setLoading(false); setFailed(true) }}
        onHttpError={(e) => {
          if (e.nativeEvent.statusCode >= 500) { setLoading(false); setFailed(true) }
        }}
        onNavigationStateChange={(nav) => setCanGoBack(nav.canGoBack)}
        allowsBackForwardNavigationGestures   // iOS swipe back
        pullToRefreshEnabled                  // Android pull-to-refresh
        startInLoadingState={false}
        domStorageEnabled
        javaScriptEnabled
        sharedCookiesEnabled                  // keep the login session
      />
      {loading && (
        <View style={styles.overlay} pointerEvents="none">
          <ActivityIndicator size="large" color="#fff" />
          <Text style={styles.loadTxt}>Memuat HCIE Tutor…</Text>
        </View>
      )}
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  fill: { flex: 1 },
  center: { flexGrow: 1, alignItems: 'center', justifyContent: 'center', padding: 32 },
  overlay: {
    position: 'absolute', top: 0, left: 0, right: 0, bottom: 0,
    alignItems: 'center', justifyContent: 'center', backgroundColor: NAVY,
  },
  loadTxt: { color: '#E6E9EF', marginTop: 14, fontSize: 15 },
  errTitle: { color: '#fff', fontSize: 20, fontWeight: '800', marginBottom: 10 },
  errBody: { color: '#C8D2E0', fontSize: 14, textAlign: 'center', lineHeight: 21, marginBottom: 22 },
  retryBtn: { backgroundColor: '#fff', paddingHorizontal: 28, paddingVertical: 11, borderRadius: 8 },
  retryTxt: { color: NAVY, fontWeight: '800', fontSize: 15 },
  errUrl: { color: '#8893A6', fontSize: 11, marginTop: 26, fontFamily: Platform.select({ ios: 'Menlo', android: 'monospace' }) },
})
