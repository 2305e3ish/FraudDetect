import React, { useState, useEffect, useRef } from 'react';
import LiveFeed from './components/LiveFeed';
import DecisionQueue from './components/DecisionQueue';

function App() {
  const [transactions, setTransactions] = useState([]);
  const [actionableQueue, setActionableQueue] = useState([]);
  const ws = useRef(null);

  useEffect(() => {
    // Connect to FastAPI WebSocket
    ws.current = new WebSocket('ws://localhost:8000/ws/stream');
    
    ws.current.onopen = () => console.log("WebSocket connected.");
    
    ws.current.onmessage = (event) => {
      const data = JSON.parse(event.data);
      // Add a unique ID for React rendering
      const tx = { ...data, _id: Date.now() + Math.random().toString(36).substr(2, 9) };
      
      setTransactions((prev) => {
        const updated = [tx, ...prev];
        return updated.slice(0, 100);
      });

      // Pin high-risk items to a separate queue that doesn't auto-delete
      if (tx.action !== 'APPROVE') {
        setActionableQueue((prev) => [tx, ...prev]);
      }
    };

    ws.current.onclose = () => console.log("WebSocket disconnected.");

    return () => {
      if (ws.current) {
        ws.current.close();
      }
    };
  }, []);

  const resolveTransaction = (id) => {
    setActionableQueue((prev) => prev.filter(tx => tx._id !== id));
  };

  return (
    <div className="min-h-screen bg-slate-900 text-slate-100 p-6 flex flex-col font-sans">
      <header className="mb-8 border-b border-slate-700 pb-4">
        <h1 className="text-3xl font-bold tracking-tight text-white flex items-center">
          <span className="w-3 h-3 rounded-full bg-emerald-500 mr-3 animate-pulse"></span>
          Adaptive Fraud Response Engine
        </h1>
        <p className="text-slate-400 mt-2">Real-time risk scoring and mitigation</p>
      </header>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 flex-grow overflow-hidden">
        {/* Left Column: Live Feed */}
        <div className="lg:col-span-1 bg-slate-800 rounded-xl border border-slate-700 p-4 flex flex-col shadow-xl">
          <h2 className="text-xl font-semibold mb-4 text-slate-200">Live Transaction Feed</h2>
          <div className="flex-grow overflow-y-auto pr-2">
            <LiveFeed transactions={transactions} />
          </div>
        </div>

        {/* Right Columns: Decision Queue */}
        <div className="lg:col-span-2 bg-slate-800 rounded-xl border border-slate-700 p-4 flex flex-col shadow-xl">
          <h2 className="text-xl font-semibold mb-4 text-slate-200">Priority Decision Queue</h2>
          <div className="flex-grow overflow-y-auto pr-2">
            <DecisionQueue transactions={actionableQueue} onResolve={resolveTransaction} />
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;
