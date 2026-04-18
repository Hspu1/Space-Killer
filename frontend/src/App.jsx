import { useState } from 'react'
import React from 'react'
import { ConfigProvider, theme, Layout, Menu } from 'antd'
import './App.css'

const { Header, Content, Sider } = Layout

function App() {
  return (
    <ConfigProvider
      theme={{
        algorithm: theme.darkAlgorithm, // темный режим по умолчанию
        token: {
          colorPrimari: '#1677ff' // акцентный цвет
        }
      }}
    >
      <Layout style={{ minHeight: '100vh' }}>
        <Sider breakpoint='lg' collapsedWidth='0'>
          <div style={{ height: 32, margin: 16, background: 'rgba(255, 255, 255, 0.2)' }}></div>
          <Menu
            theme='dark'
            mode='inline'
            defaultSelectedKeys={['1']}
            items={[
              { key: '1', label: 'Dashboard' },
              { key: '2', label: 'Map' },
              { key: '3', label: 'Chat' },
            ]}
          />
        </Sider>
        <Layout>
          <Header style={{ padding: 0, background: '#001529' }}/>
          <Content style={{ margin: '24px 16px 0' }}>
            <div style={{ padding: 24, minHeight: 360, background: '#141414', borderRadius: '8px' }}>
              <h1>Real-time Dashboard & Map</h1>
              <p>Добро пожаловать в проект! Здесь скоро будут графики и карта МКС.</p>
            </div>
          </Content>
        </Layout>
      </Layout>
    </ConfigProvider>
  )
}

export default App
