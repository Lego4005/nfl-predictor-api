import React, { useState } from 'react'
import { ChevronLeft, ChevronRight, Home, Gamepad2, Target, CreditCard, BarChart3, Users, Trophy, Settings, User, FileText, LogOut, Sun, Moon } from 'lucide-react'
import { classNames } from '../../lib/nfl-utils'
import { useTheme } from 'next-themes'
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { Gemini } from '../icons/gemini'

interface NavigationItem {
  id: string
  label: string
  icon: string
  lucideIcon?: React.ComponentType<any>
  badge?: string | number
  onClick?: () => void
}

interface NavigationSection {
  title: string
  items: NavigationItem[]
}

interface AppSidebarProps {
  currentPage: string
  onNavigate: (pageId: string) => void
  isCollapsed?: boolean
  onToggleCollapse?: () => void
  sections?: NavigationSection[]
}

interface NavigationSectionProps {
  title: string
  items: NavigationItem[]
  currentPage: string
  isCollapsed?: boolean
}

interface NavigationItemProps {
  item: NavigationItem
  isActive: boolean
  isCollapsed?: boolean
}

interface SidebarCollapseProps {
  isCollapsed: boolean
  onToggle: () => void
}

// Default navigation configuration with Lucide icons for collapsed state
const defaultSections: NavigationSection[] = [
  {
    title: 'Platform',
    items: [
      { id: 'home', label: 'Home', icon: '🏠', lucideIcon: Home }
    ]
  },
  {
    title: 'Predictions',
    items: [
      { id: 'games', label: 'Games', icon: '🏈', lucideIcon: Gamepad2 },
      { id: 'confidence-pool', label: 'Confidence Pool', icon: '🎯', lucideIcon: Target },
      { id: 'betting-card', label: 'Betting Card', icon: '🃏', lucideIcon: CreditCard },
      { id: 'performance', label: 'Model Performance', icon: '📊', lucideIcon: BarChart3 }
    ]
  },
  {
    title: 'Teams',
    items: [
      { id: 'teams', label: 'Teams', icon: '👥', lucideIcon: Users },
      { id: 'rankings', label: 'Power Rankings', icon: '🏆', lucideIcon: Trophy }
    ]
  },
  {
    title: 'Tools & More',
    items: [
      { id: 'tools', label: 'Tools', icon: '🔧', lucideIcon: Settings }
    ]
  }
]

// Individual navigation item component
function NavigationItem({ item, isActive, isCollapsed }: NavigationItemProps) {
  const IconComponent = item.lucideIcon

  return (
    <button
      onClick={item.onClick}
      className={classNames(
        'w-full text-left transition-all duration-200 flex items-center gap-3 group relative',
        isCollapsed
          ? 'px-2 py-3 rounded-xl hover:bg-white/10'
          : 'px-3 py-2.5 rounded-xl',
        isActive
          ? 'bg-primary/20 text-primary border border-primary/30'
          : isCollapsed
            ? 'text-white hover:text-primary'
            : 'hover:bg-white/5 text-gray-300 hover:text-foreground'
      )}
      title={isCollapsed ? item.label : undefined}
    >
      {isCollapsed ? (
        <div className="w-full flex justify-center py-1">
          <span className="text-2xl">{item.icon}</span>
        </div>
      ) : (
        <>
          <span className="text-lg flex-shrink-0">{item.icon}</span>
          <span className="text-sm font-medium flex-1">{item.label}</span>
          {item.badge && (
            <span className="bg-primary/20 text-primary text-xs px-2 py-0.5 rounded-full">
              {item.badge}
            </span>
          )}
        </>
      )}

      {/* Tooltip for collapsed state */}
      {isCollapsed && (
        <div className="absolute left-full ml-2 px-2 py-1 bg-foreground text-background text-xs rounded opacity-0 group-hover:opacity-100 transition-opacity pointer-events-none whitespace-nowrap z-50">
          {item.label}
        </div>
      )}
    </button>
  )
}

// Navigation section component
function NavigationSection({ title, items, currentPage, isCollapsed }: NavigationSectionProps) {
  return (
    <div className="space-y-1">
      {!isCollapsed && (
        <h3 className="px-3 py-2 text-xs font-semibold text-muted-foreground uppercase tracking-wider">
          {title}
        </h3>
      )}
      <nav className="space-y-1">
        {items.map((item) => (
          <NavigationItem
            key={item.id}
            item={item}
            isActive={item.id === currentPage}
            isCollapsed={isCollapsed}
          />
        ))}
      </nav>
      {!isCollapsed && <div className="h-4" />}
    </div>
  )
}

// Sidebar collapse toggle component
function SidebarCollapse({ isCollapsed, onToggle }: SidebarCollapseProps) {
  return (
    <button
      onClick={onToggle}
      className="absolute -right-3 top-6 bg-glass-card border border-glass-border rounded-full p-1.5 hover:bg-white/10 transition-colors z-50 shadow-lg"
      title={isCollapsed ? 'Expand sidebar' : 'Collapse sidebar'}
    >
      {isCollapsed ? (
        <ChevronRight className="w-6 h-6 text-muted-foreground" />
      ) : (
        <ChevronLeft className="w-6 h-6 text-muted-foreground" />
      )}
    </button>
  )
}

// Theme Switcher Component
function ThemeToggle({ isCollapsed }: { isCollapsed: boolean }) {
  const { setTheme, theme } = useTheme()
  // Handle the case where theme might be undefined during hydration
  const currentTheme = theme || 'dark'

  if (isCollapsed) {
    return (
      <div className="flex justify-center">
        <button
          onClick={() => setTheme(currentTheme === 'dark' ? 'light' : 'dark')}
          className="w-10 h-10 rounded-xl bg-muted hover:bg-muted/80 border border-border hover:border-primary/40 flex items-center justify-center transition-all duration-200 group"
          title={`Switch to ${currentTheme === 'dark' ? 'light' : 'dark'} mode`}
        >
          {currentTheme === 'dark' ? (
            <Sun className="w-6 h-6 text-yellow-400 group-hover:text-yellow-300 transition-colors" />
          ) : (
            <Moon className="w-6 h-6 text-blue-400 group-hover:text-blue-300 transition-colors" />
          )}
        </button>
      </div>
    )
  }

  return (
    <div className="flex justify-between items-center">
      <span className="text-sm text-muted-foreground">Theme</span>
      <div className="flex items-center bg-muted rounded-lg p-1 border border-border">
        <button
          onClick={() => setTheme('light')}
          className={classNames(
            "px-2 py-1 text-xs rounded transition-all duration-200",
            currentTheme === 'light'
              ? "bg-background text-foreground shadow-sm border border-border"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          Light
        </button>
        <button
          onClick={() => setTheme('dark')}
          className={classNames(
            "px-2 py-1 text-xs rounded transition-all duration-200",
            currentTheme === 'dark'
              ? "bg-background text-foreground shadow-sm border border-border"
              : "text-muted-foreground hover:text-foreground"
          )}
        >
          Dark
        </button>
      </div>
    </div>
  )
}

// Profile component for bottom of sidebar with dropdown functionality
function SidebarProfile({ isCollapsed }: { isCollapsed: boolean }) {
  const [isOpen, setIsOpen] = useState(false)

  // Profile data
  const profileData = {
    name: 'Eugene An',
    email: 'eugene@pickiq.ai',
    avatar: 'https://ferf1mheo22r9ira.public.blob.vercel-storage.com/profile-mjss82WnWBRO86MHHGxvJ2TVZuyrDv.jpeg',
    subscription: 'PRO',
    model: 'Gemini 2.0 Flash'
  }

  // Menu items
  const menuItems = [
    {
      label: "Profile",
      href: "#",
      icon: <User className="w-4 h-4" />,
    },
    {
      label: "Model",
      value: profileData.model,
      href: "#",
      icon: <Gemini className="w-4 h-4" />,
    },
    {
      label: "Subscription",
      value: profileData.subscription,
      href: "#",
      icon: <CreditCard className="w-4 h-4" />,
    },
    {
      label: "Settings",
      href: "#",
      icon: <Settings className="w-4 h-4" />,
    },
    {
      label: "Terms & Policies",
      href: "#",
      icon: <FileText className="w-4 h-4" />,
      external: true,
    },
  ]

  return (
    <div className="border-t border-glass-border pt-4 space-y-3">
      {/* Theme Switcher */}
      <ThemeToggle isCollapsed={isCollapsed} />

      {/* Profile Section */}
      <div className="relative">
        <DropdownMenu onOpenChange={setIsOpen}>
          {isCollapsed ? (
            <DropdownMenuTrigger asChild>
              <button className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 p-0.5 hover:scale-105 transition-transform mx-auto">
                <div className="w-full h-full rounded-full overflow-hidden bg-background">
                  <img
                    src={profileData.avatar}
                    alt={profileData.name}
                    className="w-full h-full object-cover rounded-full"
                  />
                </div>
              </button>
            </DropdownMenuTrigger>
          ) : (
            <DropdownMenuTrigger asChild>
              <button className="w-full px-3 py-3 rounded-xl bg-muted hover:bg-muted/80 transition-colors border border-border hover:border-primary/40 group">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-gradient-to-br from-purple-500 via-pink-500 to-orange-400 p-0.5 flex-shrink-0">
                    <div className="w-full h-full rounded-full overflow-hidden bg-background">
                      <img
                        src={profileData.avatar}
                        alt={profileData.name}
                        className="w-full h-full object-cover rounded-full"
                      />
                    </div>
                  </div>
                  <div className="flex-1 min-w-0 text-left">
                    <div className="text-sm font-medium text-foreground truncate">{profileData.name}</div>
                    <div className="text-xs text-muted-foreground truncate">{profileData.email}</div>
                  </div>
                  <div className="flex-shrink-0">
                    <span className="text-xs font-medium text-purple-400 bg-purple-500/10 px-2 py-1 rounded border border-purple-500/20">
                      {profileData.subscription}
                    </span>
                  </div>
                </div>
              </button>
            </DropdownMenuTrigger>
          )}

          <DropdownMenuContent
            side={isCollapsed ? "right" : "top"}
            align={isCollapsed ? "start" : "end"}
            sideOffset={isCollapsed ? 8 : 4}
            className="w-64 p-2 bg-white/95 dark:bg-zinc-900/95 backdrop-blur-sm border border-zinc-200/60 dark:border-zinc-800/60 rounded-2xl shadow-xl"
          >
            <div className="space-y-1">
              {menuItems.map((item) => (
                <DropdownMenuItem key={item.label} asChild>
                  <button
                    type="button"
                    onClick={() => {
                      if (item.external) {
                        window.open(item.href, '_blank');
                      } else {
                        console.log('Navigate to:', item.href);
                      }
                    }}
                    className="w-full flex items-center p-3 hover:bg-zinc-100/80 dark:hover:bg-zinc-800/60 rounded-xl transition-all duration-200 cursor-pointer group hover:shadow-sm border border-transparent hover:border-zinc-200/50 dark:hover:border-zinc-700/50"
                  >
                    <div className="flex items-center gap-2 flex-1">
                      {item.icon}
                      <span className="text-sm font-medium text-zinc-900 dark:text-zinc-100 tracking-tight leading-tight whitespace-nowrap group-hover:text-zinc-950 dark:group-hover:text-zinc-50 transition-colors">
                        {item.label}
                      </span>
                    </div>
                    <div className="flex-shrink-0 ml-auto">
                      {item.value && (
                        <span
                          className={classNames(
                            "text-xs font-medium rounded-md py-1 px-2 tracking-tight",
                            item.label === "Model"
                              ? "text-blue-600 bg-blue-50 dark:text-blue-400 dark:bg-blue-500/10 border border-blue-500/10"
                              : "text-purple-600 bg-purple-50 dark:text-purple-400 dark:bg-purple-500/10 border border-purple-500/10"
                          )}
                        >
                          {item.value}
                        </span>
                      )}
                    </div>
                  </button>
                </DropdownMenuItem>
              ))}
            </div>

            <DropdownMenuSeparator className="my-3 bg-gradient-to-r from-transparent via-zinc-200 to-transparent dark:via-zinc-800" />

            <DropdownMenuItem asChild>
              <button
                type="button"
                className="w-full flex items-center gap-3 p-3 duration-200 bg-red-500/10 rounded-xl hover:bg-red-500/20 cursor-pointer border border-transparent hover:border-red-500/30 hover:shadow-sm transition-all group"
              >
                <LogOut className="w-4 h-4 text-red-500 group-hover:text-red-600" />
                <span className="text-sm font-medium text-red-500 group-hover:text-red-600">
                  Sign Out
                </span>
              </button>
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>
    </div>
  )
}

// Main AppSidebar component
function AppSidebar({
  currentPage,
  onNavigate,
  isCollapsed = false,
  onToggleCollapse,
  sections = defaultSections
}: AppSidebarProps) {
  // Create navigation items with click handlers
  const sectionsWithHandlers = sections.map(section => ({
    ...section,
    items: section.items.map(item => ({
      ...item,
      onClick: () => onNavigate(item.id)
    }))
  }))

  return (
    <aside className={classNames(
      'relative flex flex-col transition-all duration-300 h-screen border-r border-glass-border',
      'bg-card',
      isCollapsed ? 'w-16' : 'w-64'
    )}>
      {/* Collapse Toggle */}
      {onToggleCollapse && (
        <SidebarCollapse isCollapsed={isCollapsed} onToggle={onToggleCollapse} />
      )}

      {/* Sidebar Header */}
      <div className="p-4 border-b border-glass-border">
        {isCollapsed ? (
          <div className="flex justify-center">
            <div className="w-8 h-8 bg-primary/20 rounded-lg flex items-center justify-center">
              <span className="text-primary font-bold text-sm">🏈</span>
            </div>
          </div>
        ) : (
          <div className="flex items-center gap-2">
            <div className="w-8 h-8 bg-primary/20 rounded-lg flex items-center justify-center">
              <span className="text-primary font-bold text-sm">🏈</span>
            </div>
            <div>
              <h1 className="font-bold text-foreground text-sm">PickIQ</h1>
              <p className="text-xs text-muted-foreground">NFL Analytics</p>
            </div>
          </div>
        )}
      </div>

      {/* Navigation Sections */}
      <div className="flex-1 p-4 overflow-y-auto overflow-x-hidden">
        {sectionsWithHandlers.map((section, index) => (
          <NavigationSection
            key={index}
            title={section.title}
            items={section.items}
            currentPage={currentPage}
            isCollapsed={isCollapsed}
          />
        ))}
      </div>

      {/* Profile Section at Bottom */}
      <div className="p-4">
        <SidebarProfile isCollapsed={isCollapsed} />
      </div>
    </aside>
  )
}

export default AppSidebar
export { NavigationSection, NavigationItem, SidebarCollapse }
export type { NavigationItem as NavigationItemType, NavigationSection as NavigationSectionType }