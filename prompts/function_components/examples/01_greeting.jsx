import './Greeting.css';

function formatName(user) {
  return `${user.firstName} ${user.lastName}`;
}

function Greeting({ user, showTime }) {
  return (
    <p className="greeting">
      Hello, {formatName(user)}!
      {showTime && <span> It is {new Date().toLocaleTimeString()}.</span>}
    </p>
  );
}

export default Greeting;
