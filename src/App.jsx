// App.jsx - Main component for our Supabase Hello World app

import { useState, useEffect } from 'react'
import { createClient } from '@supabase/supabase-js'

// Initialize Supabase client
const supabaseUrl = 'https://qhnoglsyfeafpbwpvguy.supabase.co'
const supabaseKey = process.env.REACT_APP_SUPABASE_KEY

// Check if environment variables are available
const isConfigured = supabaseUrl && supabaseKey;

// Initialize Supabase client only if properly configured
const supabase = isConfigured 
  ? createClient(supabaseUrl, supabaseKey)
  : null;

function App() {
  const [message, setMessage] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [deleting, setDeleting] = useState(null); // Track which message is being deleted

  // Fetch messages on component mount
  useEffect(() => {
    fetchMessages();
  }, []);

  // Function to fetch messages from Supabase
  const fetchMessages = async () => {
    try {
      setLoading(true);
      setError(null);
      console.log('Fetching messages...');
      
      const { data, error } = await supabase
        .from('messages')
        .select('*')
        .order('created_at', { ascending: false });
      
      if (error) {
        throw error;
      }
      
      console.log('Messages fetched:', data);
      setMessages(data || []);
    } catch (err) {
      console.error('Error fetching messages:', err.message);
      setError(`Failed to fetch messages: ${err.message}`);
    } finally {
      setLoading(false);
    }
  };

  // Function to add a new message - with debug logging
  const addMessage = async (e) => {
    e.preventDefault();
    console.log('Send button clicked');
    
    if (!message.trim()) {
      console.log('Message is empty, not sending');
      return;
    }

    try {
      console.log('Sending message:', message);
      setError(null);
      
      const { data, error } = await supabase
        .from('messages')
        .insert([{ content: message }])
        .select();
      
      if (error) {
        throw error;
      }
      
      console.log('Message sent successfully:', data);
      
      // Clear input and refresh messages
      setMessage('');
      fetchMessages();
    } catch (err) {
      console.error('Error adding message:', err.message);
      setError(`Failed to send message: ${err.message}`);
    }
  };

  // Function to delete a message
  const deleteMessage = async (id) => {
    if (!id) return;
    
    try {
      setDeleting(id);
      console.log('Deleting message with ID:', id);
      setError(null);
      
      const { error } = await supabase
        .from('messages')
        .delete()
        .eq('id', id);
      
      if (error) {
        throw error;
      }
      
      console.log('Message deleted successfully');
      
      // Update messages list without making another API call
      setMessages(messages.filter(msg => msg.id !== id));
    } catch (err) {
      console.error('Error deleting message:', err.message);
      setError(`Failed to delete message: ${err.message}`);
    } finally {
      setDeleting(null);
    }
  };

  return (
    <div className="container" style={{ maxWidth: '600px', margin: '0 auto', padding: '2rem' }}>
      <h1>Supabase Hello World</h1>
      
      {/* Show any errors */}
      {error && (
        <div style={{ 
          padding: '0.75rem', 
          backgroundColor: '#fee2e2', 
          color: '#dc2626',
          borderRadius: '4px', 
          marginBottom: '1rem' 
        }}>
          {error}
        </div>
      )}
      
      {/* Form to add a new message */}
      <form onSubmit={addMessage} style={{ marginBottom: '2rem' }}>
        <input
          type="text"
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          placeholder="Enter a message"
          style={{ 
            padding: '0.5rem', 
            width: '70%', 
            marginRight: '1rem',
            borderRadius: '4px',
            border: '1px solid #ccc'
          }}
        />
        <button 
          type="submit"
          style={{ 
            padding: '0.5rem 1rem', 
            backgroundColor: '#3ECF8E', 
            color: 'white', 
            border: 'none', 
            borderRadius: '4px',
            cursor: 'pointer',
            position: 'relative', // Ensure it's not hidden
            zIndex: '1' // Make sure it's above other elements
          }}
          onClick={() => console.log('Button clicked directly')}
        >
          Send
        </button>
      </form>
      
      {/* Display messages */}
      <div>
        <h2>Messages</h2>
        {loading ? (
          <p>Loading messages...</p>
        ) : messages.length ? (
          <ul style={{ listStyleType: 'none', padding: 0 }}>
            {messages.map((msg) => (
              <li 
                key={msg.id}
                style={{ 
                  padding: '1rem', 
                  backgroundColor: '#f9f9f9', 
                  marginBottom: '0.5rem', 
                  borderRadius: '4px',
                  border: '1px solid #eee',
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center'
                }}
              >
                <span>{msg.content}</span>
                <button
                  onClick={() => deleteMessage(msg.id)}
                  disabled={deleting === msg.id}
                  style={{
                    padding: '0.25rem 0.5rem',
                    backgroundColor: '#f87171',
                    color: 'white',
                    border: 'none',
                    borderRadius: '4px',
                    cursor: deleting === msg.id ? 'not-allowed' : 'pointer',
                    opacity: deleting === msg.id ? 0.7 : 1,
                    fontSize: '0.875rem'
                  }}
                >
                  {deleting === msg.id ? 'Deleting...' : 'Delete'}
                </button>
              </li>
            ))}
          </ul>
        ) : (
          <p>No messages yet. Be the first to say hello!</p>
        )}
      </div>
    </div>
  );
}

export default App;