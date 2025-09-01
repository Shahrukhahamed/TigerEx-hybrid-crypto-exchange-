import React, { useState } from 'react';
import Link from 'next/link';
import { useRouter } from 'next/router';
import { 
  Home, 
  TrendingUp, 
  BarChart3, 
  PieChart, 
  Target, 
  Zap, 
  Building2,
  Settings,
  Users,
  Shield,
  Wallet,
  Gift,
  ChevronDown,
  Menu,
  X
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator,
} from '@/components/ui/dropdown-menu';

interface NavigationProps {
  userRole?: 'user' | 'admin' | 'super_admin';
}

const Navigation: React.FC<NavigationProps> = ({ userRole = 'user' }) => {
  const router = useRouter();
  const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

  const isActive = (path: string) => {
    return router.pathname === path || router.pathname.startsWith(path);
  };

  const tradingMenuItems = [
    { href: '/trading/spot', label: 'Spot Trading', icon: TrendingUp },
    { href: '/trading/futures', label: 'Futures Trading', icon: BarChart3 },
    { href: '/trading/options', label: 'Options Trading', icon: Target },
    { href: '/trading/etf', label: 'ETF Trading', icon: PieChart },
    { href: '/trading/margin', label: 'Margin Trading', icon: Zap },
    { href: '/trading/alpha', label: 'Alpha Trading', icon: Building2 },
  ];

  const adminMenuItems = [
    { href: '/admin/dashboard', label: 'Dashboard', icon: Home },
    { href: '/admin/users', label: 'User Management', icon: Users },
    { href: '/admin/trading-pairs', label: 'Trading Pairs', icon: Settings },
    { href: '/admin/compliance', label: 'Compliance', icon: Shield },
    { href: '/admin/wallets', label: 'Wallet Management', icon: Wallet },
    { href: '/admin/affiliates', label: 'Affiliate System', icon: Gift },
  ];

  const NavLink: React.FC<{ href: string; children: React.ReactNode; className?: string }> = ({ 
    href, 
    children, 
    className = '' 
  }) => (
    <Link 
      href={href}
      className={`flex items-center px-3 py-2 rounded-md text-sm font-medium transition-colors ${
        isActive(href)
          ? 'bg-blue-100 text-blue-700'
          : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
      } ${className}`}
      onClick={() => setIsMobileMenuOpen(false)}
    >
      {children}
    </Link>
  );

  return (
    <nav className="bg-white shadow-sm border-b">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          {/* Logo and main navigation */}
          <div className="flex">
            {/* Logo */}
            <div className="flex-shrink-0 flex items-center">
              <Link href="/" className="text-2xl font-bold text-blue-600">
                TigerEx
              </Link>
            </div>

            {/* Desktop navigation */}
            <div className="hidden md:ml-6 md:flex md:space-x-8">
              <NavLink href="/">
                <Home className="h-4 w-4 mr-2" />
                Home
              </NavLink>

              {/* Trading dropdown */}
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button 
                    variant="ghost" 
                    className={`flex items-center px-3 py-2 text-sm font-medium ${
                      isActive('/trading') 
                        ? 'text-blue-700 bg-blue-50' 
                        : 'text-gray-600 hover:text-gray-900'
                    }`}
                  >
                    <TrendingUp className="h-4 w-4 mr-2" />
                    Trading
                    <ChevronDown className="h-4 w-4 ml-1" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="start" className="w-56">
                  {tradingMenuItems.map((item) => (
                    <DropdownMenuItem key={item.href} asChild>
                      <Link href={item.href} className="flex items-center">
                        <item.icon className="h-4 w-4 mr-2" />
                        {item.label}
                      </Link>
                    </DropdownMenuItem>
                  ))}
                </DropdownMenuContent>
              </DropdownMenu>

              <NavLink href="/portfolio">
                <Wallet className="h-4 w-4 mr-2" />
                Portfolio
              </NavLink>

              <NavLink href="/markets">
                <BarChart3 className="h-4 w-4 mr-2" />
                Markets
              </NavLink>

              {/* Admin dropdown */}
              {(userRole === 'admin' || userRole === 'super_admin') && (
                <DropdownMenu>
                  <DropdownMenuTrigger asChild>
                    <Button 
                      variant="ghost" 
                      className={`flex items-center px-3 py-2 text-sm font-medium ${
                        isActive('/admin') 
                          ? 'text-blue-700 bg-blue-50' 
                          : 'text-gray-600 hover:text-gray-900'
                      }`}
                    >
                      <Settings className="h-4 w-4 mr-2" />
                      Admin
                      <ChevronDown className="h-4 w-4 ml-1" />
                    </Button>
                  </DropdownMenuTrigger>
                  <DropdownMenuContent align="start" className="w-56">
                    {adminMenuItems.map((item) => (
                      <DropdownMenuItem key={item.href} asChild>
                        <Link href={item.href} className="flex items-center">
                          <item.icon className="h-4 w-4 mr-2" />
                          {item.label}
                        </Link>
                      </DropdownMenuItem>
                    ))}
                    {userRole === 'super_admin' && (
                      <>
                        <DropdownMenuSeparator />
                        <DropdownMenuItem asChild>
                          <Link href="/admin/super" className="flex items-center">
                            <Shield className="h-4 w-4 mr-2" />
                            Super Admin
                          </Link>
                        </DropdownMenuItem>
                      </>
                    )}
                  </DropdownMenuContent>
                </DropdownMenu>
              )}
            </div>
          </div>

          {/* Right side - User menu and mobile menu button */}
          <div className="flex items-center">
            {/* User menu */}
            <div className="hidden md:ml-4 md:flex md:items-center">
              <DropdownMenu>
                <DropdownMenuTrigger asChild>
                  <Button variant="ghost" className="flex items-center">
                    <div className="h-8 w-8 rounded-full bg-blue-600 flex items-center justify-center">
                      <span className="text-white text-sm font-medium">U</span>
                    </div>
                    <ChevronDown className="h-4 w-4 ml-2" />
                  </Button>
                </DropdownMenuTrigger>
                <DropdownMenuContent align="end" className="w-48">
                  <DropdownMenuItem asChild>
                    <Link href="/profile">Profile</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/settings">Settings</Link>
                  </DropdownMenuItem>
                  <DropdownMenuItem asChild>
                    <Link href="/security">Security</Link>
                  </DropdownMenuItem>
                  <DropdownMenuSeparator />
                  <DropdownMenuItem>
                    Sign out
                  </DropdownMenuItem>
                </DropdownMenuContent>
              </DropdownMenu>
            </div>

            {/* Mobile menu button */}
            <div className="md:hidden">
              <Button
                variant="ghost"
                size="sm"
                onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
              >
                {isMobileMenuOpen ? (
                  <X className="h-6 w-6" />
                ) : (
                  <Menu className="h-6 w-6" />
                )}
              </Button>
            </div>
          </div>
        </div>

        {/* Mobile menu */}
        {isMobileMenuOpen && (
          <div className="md:hidden">
            <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 border-t">
              <NavLink href="/">
                <Home className="h-4 w-4 mr-2" />
                Home
              </NavLink>

              {/* Trading section */}
              <div className="py-2">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-3 py-1">
                  Trading
                </div>
                {tradingMenuItems.map((item) => (
                  <NavLink key={item.href} href={item.href} className="pl-6">
                    <item.icon className="h-4 w-4 mr-2" />
                    {item.label}
                  </NavLink>
                ))}
              </div>

              <NavLink href="/portfolio">
                <Wallet className="h-4 w-4 mr-2" />
                Portfolio
              </NavLink>

              <NavLink href="/markets">
                <BarChart3 className="h-4 w-4 mr-2" />
                Markets
              </NavLink>

              {/* Admin section */}
              {(userRole === 'admin' || userRole === 'super_admin') && (
                <div className="py-2">
                  <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-3 py-1">
                    Admin
                  </div>
                  {adminMenuItems.map((item) => (
                    <NavLink key={item.href} href={item.href} className="pl-6">
                      <item.icon className="h-4 w-4 mr-2" />
                      {item.label}
                    </NavLink>
                  ))}
                  {userRole === 'super_admin' && (
                    <NavLink href="/admin/super" className="pl-6">
                      <Shield className="h-4 w-4 mr-2" />
                      Super Admin
                    </NavLink>
                  )}
                </div>
              )}

              {/* User menu */}
              <div className="py-2 border-t">
                <div className="text-xs font-semibold text-gray-500 uppercase tracking-wide px-3 py-1">
                  Account
                </div>
                <NavLink href="/profile" className="pl-6">
                  Profile
                </NavLink>
                <NavLink href="/settings" className="pl-6">
                  Settings
                </NavLink>
                <NavLink href="/security" className="pl-6">
                  Security
                </NavLink>
                <button className="w-full text-left px-9 py-2 text-sm text-gray-600 hover:text-gray-900">
                  Sign out
                </button>
              </div>
            </div>
          </div>
        )}
      </div>
    </nav>
  );
};

export default Navigation;
