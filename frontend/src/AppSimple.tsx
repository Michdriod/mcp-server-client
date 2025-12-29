// Simple test component to check if React is working
const AppSimple = () => {
  return (
    <div style={{ padding: '20px', fontFamily: 'Arial, sans-serif' }}>
      <h1>Frontend Test</h1>
      <p>If you can see this, React is working!</p>
      <p>Current time: {new Date().toLocaleTimeString()}</p>
    </div>
  );
};

export default AppSimple;