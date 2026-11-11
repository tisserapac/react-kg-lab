import { useState } from 'react';
import useTheme from '../hooks/useTheme';

export const Counter = ({ step = 1, onLimit }) => {
  const [count, setCount] = useState(0);
  const theme = useTheme();

  function handleClick() {
    const next = count + step;
    setCount(next);
    if (next >= 10) onLimit();
  }

  return (
    <button className={theme} onClick={handleClick}>
      Clicked {count} times
    </button>
  );
};

const Label = ({ text }) => <small>{text}</small>;

export function CounterWithLabel() {
  return (
    <div>
      <Label text="Try me" />
      <Counter step={2} onLimit={() => alert('Limit reached')} />
    </div>
  );
}
