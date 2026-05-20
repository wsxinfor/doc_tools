import { useState } from 'react'
import { Typography, Space, Dropdown, Button } from 'antd'
import { UserOutlined } from '@ant-design/icons'
import {
  LayoutDashboard,
  FolderOpen,
  History,
  Users,
  Settings,
  LogOut,
  ChevronRight,
} from 'lucide-react'
import { useNavigate, useLocation, Outlet } from 'react-router-dom'
import { useAuthStore } from '../../stores/authStore'
import './styles.css'
import '../../styles/global.css'

const { Text } = Typography

interface MenuItem {
  key: string
  icon: React.ReactNode
  label: string
  group?: string
}

export default function AppLayout() {
  const navigate = useNavigate()
  const location = useLocation()
  const { user, logout } = useAuthStore()
  const [collapsed, setCollapsed] = useState(false)

  const handleLogout = () => {
    logout()
    navigate('/login')
  }

  // 定义菜单项（带分组）
  const menuItems: MenuItem[] = [
    {
      key: '/documents',
      icon: <FolderOpen size={16} strokeWidth={1.5} />,
      label: '文档管理',
      group: 'core',
    },
    {
      key: '/templates',
      icon: <LayoutDashboard size={16} strokeWidth={1.5} />,
      label: '模板管理',
      group: 'core',
    },
    {
      key: '/render/history',
      icon: <History size={16} strokeWidth={1.5} />,
      label: '排版历史',
      group: 'core',
    },
    ...(user?.role === 'admin'
      ? [
          {
            key: '/admin/users',
            icon: <Users size={16} strokeWidth={1.5} />,
            label: '用户管理',
            group: 'admin',
          },
          {
            key: '/admin/settings',
            icon: <Settings size={16} strokeWidth={1.5} />,
            label: '系统设置',
            group: 'admin',
          },
        ]
      : []),
  ]

  // 按分组渲染菜单
  const renderMenuItems = (group: string) => {
    return menuItems
      .filter((item) => item.group === group)
      .map((item) => (
        <div
          key={item.key}
          className={`nav-item ${location.pathname.startsWith(item.key) ? 'active' : ''}`}
          onClick={() => navigate(item.key)}
        >
          <span className="nav-item-icon">{item.icon}</span>
          {!collapsed && (
            <>
              <span className="nav-item-label">{item.label}</span>
              {location.pathname.startsWith(item.key) && (
                <ChevronRight size={14} className="nav-item-arrow" />
              )}
            </>
          )}
        </div>
      ))
  }

  return (
    <div className="app-layout">
      {/* 侧边栏 */}
      <aside className={`sidebar ${collapsed ? 'collapsed' : ''}`}>
        {/* Logo 区 */}
        <div className="sidebar-logo" onClick={() => setCollapsed(!collapsed)}>
          <svg className="sidebar-logo-icon" viewBox="0 0 40 40" fill="none">
            <rect x="4" y="4" width="14" height="14" stroke="currentColor" strokeWidth="0.8" opacity="1" />
            <rect x="22" y="4" width="14" height="14" stroke="currentColor" strokeWidth="0.8" opacity="0.5" />
            <rect x="4" y="22" width="14" height="14" stroke="currentColor" strokeWidth="0.8" opacity="0.5" />
            <rect x="22" y="22" width="14" height="14" stroke="currentColor" strokeWidth="0.8" opacity="0.25" />
          </svg>
          {!collapsed && <span className="sidebar-logo-text">DocFormat</span>}
        </div>

        {/* 导航区 */}
        <nav className="sidebar-nav">
          {/* 核心功能分组 */}
          {!collapsed && <div className="nav-group-title">核心功能</div>}
          {renderMenuItems('core')}

          {/* 管理分组 */}
          {user?.role === 'admin' && (
            <>
              {!collapsed && <div className="nav-group-title">系统管理</div>}
              {renderMenuItems('admin')}
            </>
          )}
        </nav>

        {/* 底部用户区 */}
        {!collapsed && (
          <div className="sidebar-footer">
            <Dropdown
              menu={{
                items: [
                  {
                    key: 'logout',
                    icon: <LogOut size={14} strokeWidth={1.5} />,
                    label: '退出登录',
                    onClick: handleLogout,
                  },
                ],
              }}
              trigger={['click']}
            >
              <div className="user-info">
                <div className="user-avatar">
                  <UserOutlined />
                </div>
                <div className="user-details">
                  <div className="user-name">{user?.username}</div>
                  <div className="user-role">{user?.role === 'admin' ? '管理员' : '用户'}</div>
                </div>
                <ChevronRight size={14} className="user-arrow" />
              </div>
            </Dropdown>
          </div>
        )}
      </aside>

      {/* 主内容区 */}
      <main className="main-content">
        {/* TopBar */}
        <header className="topbar">
          <Button
            type="text"
            className="topbar-collapse-btn"
            onClick={() => setCollapsed(!collapsed)}
            icon={collapsed ? <FolderOpen size={16} strokeWidth={1.5} /> : <LayoutDashboard size={16} strokeWidth={1.5} />}
          />
          <h1 className="topbar-title">
            {menuItems.find((item) => location.pathname.startsWith(item.key))?.label ?? '工作台'}
          </h1>
          <div className="topbar-actions">
            <Space>
              <Text className="user-greeting">{user?.username}</Text>
            </Space>
          </div>
        </header>

        {/* 内容区 */}
        <div className="page-body">
          <Outlet />
        </div>
      </main>
    </div>
  )
}
