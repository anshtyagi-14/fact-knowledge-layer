import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { BrowserRouter, Routes, Route, Link, useLocation } from 'react-router-dom'
import Dashboard from './pages/Dashboard'
import DocumentView from './pages/DocumentView'
import FactExplorer from './pages/FactExplorer'
import RelationshipExplorer from './pages/RelationshipExplorer'
import clsx from 'clsx'

const queryClient = new QueryClient()

function NavLinks() {
  const location = useLocation()
  
  const links = [
    { path: '/', label: 'Dashboard' },
    { path: '/facts', label: 'Fact Explorer' },
    { path: '/relationships', label: 'Relationships' }
  ]
  
  return (
    <div className="flex gap-6">
      {links.map(l => (
        <Link 
          key={l.path} 
          to={l.path} 
          className={clsx(
            "font-medium hover:text-blue-600 transition-colors",
            location.pathname === l.path ? "text-blue-600" : "text-gray-600"
          )}
        >
          {l.label}
        </Link>
      ))}
    </div>
  )
}

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <div className="min-h-screen bg-gray-50 flex flex-col">
          <nav className="bg-white shadow-sm px-6 py-4">
            <div className="max-w-7xl mx-auto flex items-center justify-between">
              <Link to="/" className="text-xl font-bold text-gray-900">Fact Knowledge Layer</Link>
              <NavLinks />
            </div>
          </nav>
          
          <main className="flex-1 max-w-7xl w-full mx-auto p-6">
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/documents/:id" element={<DocumentView />} />
              <Route path="/facts" element={<FactExplorer />} />
              <Route path="/relationships" element={<RelationshipExplorer />} />
            </Routes>
          </main>
        </div>
      </BrowserRouter>
    </QueryClientProvider>
  )
}

export default App
