import React, { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import axios from 'axios';
import { Link } from 'react-router-dom';
import { FileUp, FileText, CheckCircle, AlertCircle } from 'lucide-react';

const API_URL = 'http://localhost:8000';

export default function Dashboard() {
  const [file, setFile] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  
  const { data: stats } = useQuery({
    queryKey: ['stats'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/stats`);
      return res.data;
    },
    refetchInterval: 5000
  });

  const { data: documents, refetch: refetchDocs } = useQuery({
    queryKey: ['documents'],
    queryFn: async () => {
      const res = await axios.get(`${API_URL}/documents`);
      return res.data;
    },
    refetchInterval: 5000
  });

  const handleUpload = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;
    
    setUploading(true);
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      await axios.post(`${API_URL}/documents`, formData);
      setFile(null);
      refetchDocs();
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  return (
    <div className="space-y-8">
      {/* Upload Zone */}
      <div className="bg-white p-8 rounded-xl shadow-sm border border-gray-100 flex flex-col items-center justify-center">
        <h2 className="text-xl font-semibold mb-4">Upload Document</h2>
        <form onSubmit={handleUpload} className="flex gap-4 items-center">
          <input 
            type="file" 
            accept=".pdf"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="border p-2 rounded"
          />
          <button 
            type="submit" 
            disabled={!file || uploading}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 disabled:opacity-50 flex items-center gap-2"
          >
            <FileUp size={20} />
            {uploading ? 'Uploading...' : 'Upload & Process'}
          </button>
        </form>
      </div>

      {/* Stats */}
      {stats && (
        <div className="grid grid-cols-4 gap-4">
          <div className="bg-white p-6 rounded-xl shadow-sm border border-gray-100">
            <div className="text-gray-500 text-sm">Total Facts</div>
            <div className="text-3xl font-bold mt-1">{stats.total_facts}</div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-green-100">
            <div className="text-green-600 text-sm">Corroborates</div>
            <div className="text-3xl font-bold mt-1">{<Link to='/relationships'>{stats.relationships?.CORROBORATES || 0}</Link>}</div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-red-100">
            <div className="text-red-600 text-sm">Contradicts</div>
            <div className="text-3xl font-bold mt-1">{<Link to='/relationships'>{stats.relationships?.CONTRADICTS || 0}</Link>}</div>
          </div>
          <div className="bg-white p-6 rounded-xl shadow-sm border border-yellow-100">
            <div className="text-yellow-600 text-sm">Reconciled</div>
            <div className="text-3xl font-bold mt-1">{<Link to='/relationships'>{stats.relationships?.RECONCILED || 0}</Link>}</div>
          </div>
        </div>
      )}

      {/* Document List */}
      <div>
        <h2 className="text-xl font-semibold mb-4">Processed Documents</h2>
        <div className="bg-white rounded-xl shadow-sm border border-gray-100 divide-y">
          {documents?.length === 0 && (
             <div className="p-6 text-center text-gray-500">No documents yet. Upload one above.</div>
          )}
          {documents?.map((doc: any) => (
            <Link key={doc.id} to={`/documents/${doc.id}`} className="block p-4 hover:bg-gray-50 flex items-center justify-between">
              <div className="flex items-center gap-4">
                <FileText className="text-blue-500" />
                <div>
                  <div className="font-medium text-gray-900">{doc.title}</div>
                  <div className="text-sm text-gray-500">Pages: {doc.page_count}</div>
                </div>
              </div>
              <div className="flex items-center gap-2">
                {doc.status === 'complete' ? (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-green-100 text-green-700 text-sm font-medium">
                    <CheckCircle size={16} /> Complete
                  </span>
                ) : doc.status === 'failed' ? (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-red-100 text-red-700 text-sm font-medium">
                    <AlertCircle size={16} /> Failed
                  </span>
                ) : (
                  <span className="inline-flex items-center gap-1 px-3 py-1 rounded-full bg-blue-100 text-blue-700 text-sm font-medium animate-pulse">
                    Processing ({doc.status})
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>
      </div>
    </div>
  );
}
