import React from 'react';

const DecisionQueue = ({ transactions, onResolve }) => {
  // We no longer need to filter APPROVE because actionableQueue already filters it
  const actionableTx = transactions;

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {actionableTx.map((tx) => {
        let borderColor = '';
        let bgColor = '';
        let icon = '';

        if (tx.action === 'OTP_CHALLENGE') {
          borderColor = 'border-yellow-500/50';
          bgColor = 'bg-yellow-950/30';
          icon = '🟡';
        } else if (tx.action === 'MANUAL_REVIEW') {
          borderColor = 'border-orange-500/50';
          bgColor = 'bg-orange-950/30';
          icon = '🟠';
        } else if (tx.action === 'BLOCK') {
          borderColor = 'border-red-500/50';
          bgColor = 'bg-red-950/30';
          icon = '🔴';
        }

        return (
          <div key={tx._id} className={`p-4 rounded-xl border ${borderColor} ${bgColor} flex flex-col shadow-lg`}>
            <div className="flex justify-between items-start mb-3 border-b border-slate-700/50 pb-2">
              <div>
                <div className="text-xs text-slate-400 font-mono mb-1">{tx.user_id}</div>
                <div className="text-2xl font-bold">${tx.amount.toFixed(2)}</div>
              </div>
              <div className="flex flex-col items-end">
                <span className="font-bold text-sm tracking-wider">{icon} {tx.action.replace('_', ' ')}</span>
                <span className="text-xs text-slate-400 mt-1">Score: <span className="text-slate-200 font-mono">{tx.score.toFixed(1)}</span></span>
              </div>
            </div>
            
            <div className="flex-grow">
              <h4 className="text-xs text-slate-400 uppercase tracking-wider mb-2">Detected Risk Factors</h4>
              <ul className="space-y-1">
                {tx.risk_factors.map((factor, idx) => (
                  <li key={idx} className="text-sm flex items-start">
                    <span className="text-red-400 mr-2">!</span>
                    <span className="text-slate-300">{factor}</span>
                  </li>
                ))}
                {tx.risk_factors.length === 0 && (
                  <li className="text-sm text-slate-500 italic">No explicit factors mapped.</li>
                )}
              </ul>
            </div>
            
            <div className="mt-4 pt-3 flex gap-2 border-t border-slate-700/50">
              {tx.action === 'MANUAL_REVIEW' && (
                <>
                  <button onClick={() => onResolve(tx._id)} className="flex-1 bg-emerald-600 hover:bg-emerald-500 text-white text-xs font-semibold py-2 rounded transition-colors">Approve</button>
                  <button onClick={() => onResolve(tx._id)} className="flex-1 bg-red-600 hover:bg-red-500 text-white text-xs font-semibold py-2 rounded transition-colors">Block</button>
                </>
              )}
              {tx.action === 'OTP_CHALLENGE' && (
                <button onClick={() => onResolve(tx._id)} className="flex-1 bg-slate-700 hover:bg-slate-600 text-white text-xs font-semibold py-2 rounded transition-colors">View Step-Up Details</button>
              )}
              {tx.action === 'BLOCK' && (
                <button onClick={() => onResolve(tx._id)} className="flex-1 bg-slate-800 border border-slate-600 text-slate-300 text-xs font-semibold py-2 rounded transition-colors hover:bg-slate-700">Acknowledge</button>
              )}
            </div>
          </div>
        );
      })}

      {actionableTx.length === 0 && (
        <div className="col-span-full flex flex-col items-center justify-center p-12 border-2 border-dashed border-slate-700 rounded-xl">
          <div className="text-4xl mb-4">☕</div>
          <h3 className="text-lg font-medium text-slate-300">Inbox Zero</h3>
          <p className="text-slate-500 text-sm mt-1">No actionable alerts in the queue.</p>
        </div>
      )}
    </div>
  );
};

export default DecisionQueue;
