import React from 'react';
import { PieChart, Pie, Cell, ResponsiveContainer } from 'recharts';
import { Activity, Cpu, Zap, Play, CheckCircle, AlertTriangle } from 'lucide-react';
import { motion } from 'framer-motion';

const MetricRing = ({ value, label, color, icon: Icon }) => {
    const data = [
        { value: value },
        { value: 100 - value },
    ];

    return (
        <div className="bg-surface border border-border rounded-xl p-6 flex flex-col items-center relative overflow-hidden group hover:border-primary/50 transition-colors">
            <div className="absolute inset-0 bg-gradient-to-br from-transparent to-primary/5 opacity-0 group-hover:opacity-100 transition-opacity" />

            <div className="relative w-32 h-32">
                <ResponsiveContainer width="100%" height="100%">
                    <PieChart>
                        <Pie
                            data={data}
                            cx="50%"
                            cy="50%"
                            innerRadius={50}
                            outerRadius={60}
                            startAngle={90}
                            endAngle={-270}
                            dataKey="value"
                            stroke="none"
                        >
                            <Cell fill={color} />
                            <Cell fill="#333" />
                        </Pie>
                    </PieChart>
                </ResponsiveContainer>
                <div className="absolute inset-0 flex items-center justify-center flex-col">
                    <Icon size={24} style={{ color }} className="mb-1" />
                    <span className="text-2xl font-bold font-mono">{value}%</span>
                </div>
            </div>
            <span className="mt-4 text-text-dim font-medium uppercase tracking-wider text-sm">{label}</span>
        </div>
    );
};

const AgentCard = ({ name, status, role }) => (
    <div className="bg-surface border border-border rounded-xl p-4 flex items-center justify-between hover:bg-surface-highlight transition-colors">
        <div className="flex items-center gap-4">
            <div className={`w-3 h-3 rounded-full ${status === 'active' ? 'bg-primary animate-pulse' : 'bg-text-dim'}`} />
            <div>
                <h3 className="font-bold text-lg">{name}</h3>
                <p className="text-text-dim text-sm">{role}</p>
            </div>
        </div>
        <span className={`px-3 py-1 rounded-full text-xs font-mono uppercase ${status === 'active' ? 'bg-primary-dim text-primary border border-primary/20' : 'bg-surface text-text-dim border border-border'
            }`}>
            {status}
        </span>
    </div>
);

const QuickAction = ({ label, icon: Icon, color }) => (
    <button className="flex flex-col items-center justify-center p-4 bg-surface border border-border rounded-xl hover:bg-surface-highlight hover:scale-105 transition-all group">
        <div className={`p-3 rounded-full mb-3 bg-${color}-dim text-${color} group-hover:shadow-lg group-hover:shadow-${color}/20 transition-shadow`}>
            <Icon size={24} />
        </div>
        <span className="font-medium">{label}</span>
    </button>
);

const Dashboard = () => {
    return (
        <div className="p-8 space-y-8 max-w-7xl mx-auto">
            <header className="flex justify-between items-end">
                <div>
                    <h2 className="text-3xl font-bold text-white mb-2">Command Center</h2>
                    <p className="text-text-dim">System Status: <span className="text-primary">OPERATIONAL</span></p>
                </div>
                <div className="flex gap-2">
                    <span className="px-3 py-1 bg-surface border border-border rounded text-xs font-mono text-text-dim">v2.0.0-alpha</span>
                </div>
            </header>

            {/* Metrics Grid */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                <MetricRing value={42} label="CPU Load" color="#00ff9d" icon={Cpu} />
                <MetricRing value={78} label="GPU Usage" color="#00d2ff" icon={Zap} />
                <MetricRing value={24} label="Memory" color="#ff0055" icon={Activity} />
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
                {/* Active Agents */}
                <div className="lg:col-span-2 space-y-4">
                    <h3 className="text-xl font-bold flex items-center gap-2">
                        <Activity size={20} className="text-primary" />
                        Active Agents
                    </h3>
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                        <AgentCard name="Maestro" role="Orchestrator" status="active" />
                        <AgentCard name="Quality Guardian" role="Validation" status="active" />
                        <AgentCard name="Resource Monitor" role="System" status="idle" />
                        <AgentCard name="Prompt Refiner" role="Generation" status="idle" />
                    </div>
                </div>

                {/* Quick Actions */}
                <div className="space-y-4">
                    <h3 className="text-xl font-bold flex items-center gap-2">
                        <Zap size={20} className="text-secondary" />
                        Quick Actions
                    </h3>
                    <div className="grid grid-cols-2 gap-4">
                        <QuickAction label="Generate" icon={Play} color="primary" />
                        <QuickAction label="Validate" icon={CheckCircle} color="secondary" />
                        <QuickAction label="Emergency" icon={AlertTriangle} color="accent" />
                    </div>
                </div>
            </div>
        </div>
    );
};

export default Dashboard;
