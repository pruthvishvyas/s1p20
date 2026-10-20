import { Component } from 'react';

export class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { failed: false, msg: '' }; }
  static getDerivedStateFromError(e) { return { failed: true, msg: e && e.message ? e.message : 'Unknown error' }; }
  componentDidCatch(e) { console.error('Panel error:', e); }
  render() {
    if (this.state.failed) return <div className="empty-state"><p className="empty-message">This panel could not be displayed.</p><p className="empty-action">{this.state.msg}</p></div>;
    return this.props.children;
  }
}
