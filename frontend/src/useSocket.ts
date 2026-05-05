import { useEffect, useRef, useCallback, useState } from 'react';

export interface TabStatus {
  tab_id: number;
  phone: string;
  username: string;
  status: string;
  activation_id: string;
}

export interface Account {
  username: string;
  password: string;
  full_name: string;
  phone: string;
  status: string;
}

export interface OTPRequest {
  activation_id: string;
  phone: string;
}

export interface JobState {
  job_id: string;
  running: boolean;
  total: number;
  success: number;
  failed: number;
  in_progress: number;
  tabs: Record<string, TabStatus>;
  created_accounts: Account[];
  elapsed: number;
}

const INITIAL_STATE: JobState = {
  job_id: '',
  running: false,
  total: 0,
  success: 0,
  failed: 0,
  in_progress: 0,
  tabs: {},
  created_accounts: [],
  elapsed: 0,
};

export function useSocket() {
  const wsRef = useRef<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [state, setState] = useState<JobState>(INITIAL_STATE);
  const [otpRequests, setOtpRequests] = useState<OTPRequest[]>([]);
  const [logs, setLogs] = useState<string[]>([]);
  const reconnectTimer = useRef<ReturnType<typeof setTimeout>>(undefined);

  const addLog = useCallback((msg: string) => {
    setLogs(prev => [...prev.slice(-200), `[${new Date().toLocaleTimeString()}] ${msg}`]);
  }, []);

  const connect = useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;

    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
    const wsUrl = `${protocol}//${window.location.host}/ws`;
    const ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      setConnected(true);
      addLog('Connected to server');
    };

    ws.onclose = () => {
      setConnected(false);
      addLog('Disconnected — reconnecting...');
      reconnectTimer.current = setTimeout(connect, 3000);
    };

    ws.onerror = () => {
      ws.close();
    };

    ws.onmessage = (e) => {
      try {
        const msg = JSON.parse(e.data);
        const event = msg.event;

        switch (event) {
          case 'INIT':
            setState({
              job_id: msg.job_id || '',
              running: msg.running || false,
              total: msg.total || 0,
              success: msg.success || 0,
              failed: msg.failed || 0,
              in_progress: msg.in_progress || 0,
              tabs: msg.tabs || {},
              created_accounts: msg.created_accounts || [],
              elapsed: msg.elapsed || 0,
            });
            break;

          case 'JOB_STARTED':
            setState(prev => ({ ...prev, running: true, job_id: msg.job_id, total: msg.total }));
            addLog(`Job started: ${msg.total} accounts`);
            break;

          case 'JOB_STOPPED':
            setState(prev => ({ ...prev, running: false }));
            addLog('Job stopped');
            break;

          case 'JOB_COMPLETE':
            setState(prev => ({
              ...prev,
              running: false,
              success: msg.success ?? prev.success,
              failed: msg.failed ?? prev.failed,
              elapsed: msg.elapsed ?? prev.elapsed,
            }));
            addLog(`Job complete: ${msg.success} success, ${msg.failed} failed`);
            break;

          case 'TAB_STATUS':
            setState(prev => ({
              ...prev,
              tabs: {
                ...prev.tabs,
                [msg.tab_id]: {
                  tab_id: msg.tab_id,
                  phone: msg.phone,
                  username: msg.username,
                  status: msg.status,
                  activation_id: msg.activation_id || '',
                },
              },
            }));
            break;

          case 'OTP_NEEDED':
            setOtpRequests(prev => {
              if (prev.find(r => r.activation_id === msg.activation_id)) return prev;
              return [...prev, { activation_id: msg.activation_id, phone: msg.phone }];
            });
            addLog(`OTP needed for ${msg.phone}`);
            break;

          case 'ACCOUNT_CREATED':
            setState(prev => ({
              ...prev,
              success: prev.success + 1,
              created_accounts: [...prev.created_accounts, msg as Account],
            }));
            addLog(`Account created: ${msg.username}`);
            break;

          case 'PONG':
            break;

          default:
            break;
        }
      } catch {
        // ignore parse errors
      }
    };

    wsRef.current = ws;
  }, [addLog]);

  useEffect(() => {
    connect();
    return () => {
      clearTimeout(reconnectTimer.current);
      wsRef.current?.close();
    };
  }, [connect]);

  const sendOtp = useCallback((activationId: string, otp: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        event: 'SUBMIT_OTP',
        activation_id: activationId,
        otp,
      }));
      setOtpRequests(prev => prev.filter(r => r.activation_id !== activationId));
      addLog(`OTP submitted for ${activationId}`);
    }
  }, [addLog]);

  return { connected, state, otpRequests, logs, sendOtp };
}
