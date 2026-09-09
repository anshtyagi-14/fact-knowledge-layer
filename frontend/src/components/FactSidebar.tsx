
import { ShieldAlert, ShieldCheck } from 'lucide-react';
import clsx from 'clsx';

interface FactSidebarProps {
  facts: any[];
  activeFactId: string | null;
  onFactClick: (id: string, bbox: any) => void;
  showUnverified: boolean;
  onToggleUnverified: (val: boolean) => void;
}

export default function FactSidebar({ facts, activeFactId, onFactClick, showUnverified, onToggleUnverified }: FactSidebarProps) {
  const visibleFacts = facts.filter(f => showUnverified || f.status === 'verified');

  return (
    <div className="flex flex-col h-full bg-white border border-gray-200 rounded shadow-sm">
      <div className="p-4 border-b border-gray-200 flex justify-between items-center bg-gray-50 rounded-t">
        <h3 className="font-semibold text-gray-800">Extracted Facts</h3>
        <label className="flex items-center gap-2 text-sm text-gray-600 cursor-pointer">
          <input 
            type="checkbox" 
            checked={showUnverified} 
            onChange={(e) => onToggleUnverified(e.target.checked)}
            className="rounded text-blue-600 focus:ring-blue-500"
          />
          Show Unverified
        </label>
      </div>
      
      <div className="flex-1 overflow-y-auto p-2 space-y-2">
        {visibleFacts.length === 0 && (
          <div className="p-4 text-center text-gray-500 text-sm">No facts found on this page.</div>
        )}
        {visibleFacts.map(fact => (
          <div 
            key={fact.id}
            onClick={() => {
                // Determine best bbox to show. Sometimes Gemini returns a list of dicts, sometimes it's mapped to the block.
                // In our backend, parser gets a list of block bboxes. The verifier doesn't natively map evidence_text to the exact bbox yet.
                // For this assignment, we'll assume evidence_bbox is available or fallback to the first block bbox if we mapped it.
                // If evidence_bbox is null, we won't highlight.
                onFactClick(fact.id, fact.evidence_bbox)
            }}
            className={clsx(
              "p-3 rounded-lg border cursor-pointer transition-colors text-sm",
              activeFactId === fact.id ? "bg-blue-50 border-blue-200" : "bg-white border-gray-100 hover:border-gray-300"
            )}
          >
            <div className="flex justify-between items-start mb-1">
              <span className="font-medium text-gray-900">{fact.subject}</span>
              {fact.status === 'verified' ? (
                 <ShieldCheck size={16} className="text-green-500"  />
              ) : (
                 <ShieldAlert size={16} className="text-orange-500"  />
              )}
            </div>
            <div className="text-gray-600 mb-2">
              <span className="font-semibold text-gray-700">{fact.predicate}:</span> {fact.raw_value}
            </div>
            <div className="text-xs text-gray-400 bg-gray-50 p-2 rounded italic border border-gray-100">
              "{fact.evidence_text}"
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
