import React, { useEffect, useState } from 'react';

const LiveFeed = ({ transactions }) => {
  // Only show the APPROVE and low severity items here, or show all but fade out APPROVE
  return (
    <div className="flex flex-col gap-2">
      {transactions.map((tx) => {
        const isApprove = tx.action === 'APPROVE';
        
        return (
          <div 
            key={tx._id} 
            className={`p-3 rounded-lg border text-sm flex justify-between items-center transition-all duration-500 ease-in-out ${
              isApprove 
                ? 'bg-emerald-900/20 border-emerald-800/30 text-emerald-100 opacity-60 hover:opacity-100' 
                : 'bg-slate-700/50 border-slate-600 text-slate-100'
            }`}
          >
            <div>
              <span className="font-mono text-slate-400 mr-2">{tx.user_id}</span>
              <span className="font-semibold">${tx.amount.toFixed(2)}</span>
            </div>
            <div className="flex items-center gap-3">
              <span className={`px-2 py-0.5 rounded text-xs font-bold ${
                tx.action === 'APPROVE' ? 'bg-emerald-500/20 text-emerald-400' :
                tx.action === 'OTP_CHALLENGE' ? 'bg-yellow-500/20 text-yellow-400' :
                tx.action === 'MANUAL_REVIEW' ? 'bg-orange-500/20 text-orange-400' :
                'bg-red-500/20 text-red-400'
              }`}>
                {tx.action}
              </span>
              <span className="text-xs text-slate-500">{tx.latency_ms}ms</span>
            </div>
          </div>
        );
      })}
      
      {transactions.length === 0 && (
        <div className="text-slate-500 text-center py-8 italic">Waiting for transactions...</div>
      )}
    </div>
  );
};

export default LiveFeed;
