import React from 'react';
import { NavLink, Outlet } from 'react-router-dom';
import { LayoutDashboard, Workflow, Settings, Activity, Terminal } from 'lucide-react';
import clsx from 'clsx';

const SidebarItem = ({ to, icon: Icon, label }) => (
    <NavLink
        to={to}
        className={({ isActive }) =>
            clsx(
                "flex items-center gap-3 px-4 py-3 rounded-lg transition-all duration-200 group",
                isActive
                    ? "bg-primary-dim text-primary border-r-2 border-primary"
                    : "text-text-dim hover:text-text hover:bg-surface-highlight"
            )
        }
    >
        <Icon size={20} className="group-hover:scale-110 transition-transform" />
        <span className="font-medium">{label}</span>
    </NavLink>
);

const Layout = () => {
    return (
        <div className="flex h-screen bg-background text-text font-sans overflow-hidden">
            {/* Sidebar */}
            <aside className="w-64 bg-surface border-r border-border flex flex-col">
                <div className="p-6 border-b border-border">
                    <h1 className="text-2xl font-bold text-transparent bg-clip-text bg-gradient-to-r from-primary to-secondary font-mono tracking-tighter">
                        VAULTMIND
                        <span className="text-xs block text-text-dim tracking-widest mt-1">FORGE v2.0</span>
                    </h1>
                </div>

                <nav className="flex-1 p-4 space-y-2">
                    <SidebarItem to="/" icon={LayoutDashboard} label="Dashboard" />
                    <SidebarItem to="/studio" icon={Workflow} label="Workflow Studio" />
                    <SidebarItem to="/monitoring" icon={Activity} label="Monitoring" />
                    <SidebarItem to="/terminal" icon={Terminal} label="Terminal" />
                </nav>

                <div className="p-4 border-t border-border">
                    <SidebarItem to="/settings" icon={Settings} label="Settings" />
                </div>
            </aside>

            {/* Main Content */}
            <main className="flex-1 overflow-auto relative">
                {/* Background Grid Effect */}
                <div className="absolute inset-0 pointer-events-none opacity-[0.02]"
                    style={{ backgroundImage: 'radial-gradient(#ffffff 1px, transparent 1px)', backgroundSize: '24px 24px' }}>
                </div>

                <Outlet />
            </main>
        </div>
    );
};

export default Layout;
