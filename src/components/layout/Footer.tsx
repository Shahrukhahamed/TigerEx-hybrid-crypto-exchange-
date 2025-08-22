'use client'

import Link from 'next/link'
import { motion } from 'framer-motion'

export function Footer() {
  const footerSections = [
    {
      title: 'Products',
      links: [
        { name: 'Spot Trading', href: '/spot' },
        { name: 'Futures Trading', href: '/futures' },
        { name: 'Options Trading', href: '/options' },
        { name: 'Copy Trading', href: '/copy-trading' },
        { name: 'Earn Products', href: '/earn' },
        { name: 'NFT Marketplace', href: '/nft' },
      ]
    },
    {
      title: 'Services',
      links: [
        { name: 'Institutional', href: '/institutional' },
        { name: 'API Trading', href: '/api' },
        { name: 'Launchpad', href: '/launchpad' },
        { name: 'P2P Trading', href: '/p2p' },
        { name: 'OTC Trading', href: '/otc' },
        { name: 'Custody', href: '/custody' },
      ]
    },
    {
      title: 'Support',
      links: [
        { name: 'Help Center', href: '/help' },
        { name: 'API Documentation', href: '/docs' },
        { name: 'Trading Fees', href: '/fees' },
        { name: 'Security', href: '/security' },
        { name: 'Bug Bounty', href: '/bug-bounty' },
        { name: 'Contact Us', href: '/contact' },
      ]
    },
    {
      title: 'Company',
      links: [
        { name: 'About Us', href: '/about' },
        { name: 'Careers', href: '/careers' },
        { name: 'Blog', href: '/blog' },
        { name: 'Press', href: '/press' },
        { name: 'Legal', href: '/legal' },
        { name: 'Privacy Policy', href: '/privacy' },
      ]
    }
  ]

  const socialLinks = [
    { name: 'Twitter', href: 'https://twitter.com/tigerex', icon: '𝕏' },
    { name: 'Discord', href: 'https://discord.gg/tigerex', icon: '💬' },
    { name: 'Telegram', href: 'https://t.me/tigerex', icon: '✈️' },
    { name: 'GitHub', href: 'https://github.com/tigerex', icon: '🐙' },
  ]

  return (
    <footer className="bg-gray-900 border-t border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-8">
          {/* Brand Section */}
          <div className="lg:col-span-1">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
            >
              <Link href="/" className="flex items-center space-x-2 mb-4">
                <div className="w-8 h-8 bg-gradient-to-r from-orange-500 to-red-500 rounded-lg flex items-center justify-center">
                  <span className="text-white font-bold text-lg">T</span>
                </div>
                <span className="text-white font-bold text-xl">TigerEx</span>
              </Link>
              <p className="text-gray-400 text-sm mb-6">
                The world's most advanced hybrid cryptocurrency exchange platform.
              </p>
              
              {/* Social Links */}
              <div className="flex space-x-4">
                {socialLinks.map((social) => (
                  <a
                    key={social.name}
                    href={social.href}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="w-10 h-10 bg-gray-800 hover:bg-orange-500 rounded-lg flex items-center justify-center transition-colors"
                  >
                    <span className="text-lg">{social.icon}</span>
                  </a>
                ))}
              </div>
            </motion.div>
          </div>

          {/* Footer Links */}
          {footerSections.map((section, sectionIndex) => (
            <div key={section.title}>
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.6, delay: sectionIndex * 0.1 }}
              >
                <h3 className="text-white font-semibold mb-4">{section.title}</h3>
                <ul className="space-y-2">
                  {section.links.map((link) => (
                    <li key={link.name}>
                      <Link
                        href={link.href}
                        className="text-gray-400 hover:text-orange-400 text-sm transition-colors"
                      >
                        {link.name}
                      </Link>
                    </li>
                  ))}
                </ul>
              </motion.div>
            </div>
          ))}
        </div>

        {/* Bottom Section */}
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.6, delay: 0.8 }}
          className="mt-12 pt-8 border-t border-gray-800"
        >
          <div className="flex flex-col md:flex-row justify-between items-center">
            <div className="text-gray-400 text-sm mb-4 md:mb-0">
              © 2024 TigerEx. All rights reserved.
            </div>
            
            <div className="flex flex-wrap gap-6 text-sm">
              <Link href="/terms" className="text-gray-400 hover:text-orange-400 transition-colors">
                Terms of Service
              </Link>
              <Link href="/privacy" className="text-gray-400 hover:text-orange-400 transition-colors">
                Privacy Policy
              </Link>
              <Link href="/cookies" className="text-gray-400 hover:text-orange-400 transition-colors">
                Cookie Policy
              </Link>
              <Link href="/risk" className="text-gray-400 hover:text-orange-400 transition-colors">
                Risk Disclosure
              </Link>
            </div>
          </div>
          
          <div className="mt-4 text-center text-xs text-gray-500">
            TigerEx is a technology company and does not provide investment advice. 
            Cryptocurrency trading involves substantial risk of loss.
          </div>
        </motion.div>
      </div>
    </footer>
  )
}