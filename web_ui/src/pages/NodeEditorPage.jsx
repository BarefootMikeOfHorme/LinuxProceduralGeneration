import React, { useState } from 'react';
import { ReactFlowProvider } from 'reactflow';
import NodeEditor from '../components/NodeEditor';
import NodePalette from '../components/NodePalette';
import PropertyPanel from '../components/PropertyPanel';
import Toolbar from '../components/Toolbar';
import FileBrowser from '../components/FileBrowser';
import OutputModal from '../components/OutputModal';
import ExecutionPanel from '../components/ExecutionPanel';
import useKeyboardShortcuts from '../hooks/useKeyboardShortcuts';
import { useWorkflowStore } from '../store/workflowStore';
import { showHelpDialog } from '../utils/notifications';

const NodeEditorPage = () => {
    const [showPalette, setShowPalette] = useState(true);
    const [showProperties, setShowProperties] = useState(true);
    const [selectedNode, setSelectedNode] = useState(null);
    const { executeWorkflow, saveWorkflow } = useWorkflowStore();

    useKeyboardShortcuts({
        'shift+a': () => setShowPalette(true),
        'f5': () => executeWorkflow(),
        'ctrl+s': (e) => {
            e.preventDefault();
            saveWorkflow('Untitled Workflow', 'Auto-saved workflow');
        },
        'f1': () => showHelpDialog('VaultMind Forge Keyboard Shortcuts', [
            { key: 'Shift+A', action: 'Add node' },
            { key: 'F5', action: 'Execute workflow' },
            { key: 'Ctrl+S', action: 'Save workflow' },
            { key: 'Del', action: 'Delete selected node' },
            { key: 'M', action: 'Mute node' },
            { key: 'Ctrl+A', action: 'Toggle AI assist' },
            { key: 'F1', action: 'Show this help' },
            { key: 'Esc', action: 'Deselect node' },
        ]),
        'escape': () => setSelectedNode(null),
    });

    return (
        <ReactFlowProvider>
            <div className="flex flex-col h-full bg-background">
                <Toolbar
                    showPalette={showPalette}
                    setShowPalette={setShowPalette}
                    showProperties={showProperties}
                    setShowProperties={setShowProperties}
                />
                <div className="flex flex-1 overflow-hidden relative">
                    {showPalette && (
                        <div className="absolute left-0 top-0 bottom-0 z-10">
                            <NodePalette />
                        </div>
                    )}

                    <div className="flex-1 h-full">
                        <NodeEditor onNodeSelect={setSelectedNode} />
                    </div>

                    {showProperties && selectedNode && (
                        <div className="absolute right-0 top-0 bottom-0 z-10">
                            <PropertyPanel node={selectedNode} />
                        </div>
                    )}
                </div>
            </div>

            {/* Modals and Panels - controlled by Zustand store */}
            <FileBrowser />
            <OutputModal />
            <ExecutionPanel />
        </ReactFlowProvider>
    );
};

export default NodeEditorPage;
