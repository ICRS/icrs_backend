import { useState } from "react";

function useForm({ additionalData }) {
  const [status, setStatus] = useState('');
  const [message, setMessage] = useState('');

  const handleSubmit = (e) => {
    e.preventDefault();
    setStatus('loading');

    const finalFormEndpoint = e.target.action;
    const data = Array.from(e.target.elements)
      .filter((input) => input.name)
      .reduce((obj, input) => Object.assign(obj, { [input.name]: input.value }), {});

    console.log(data, finalFormEndpoint);

    fetch(finalFormEndpoint, {
      method: 'POST',
      headers: {
        "Accept": "*/*",
      },
      body: JSON.stringify(data),
    })
      .then((response) => {
        if (!response.ok) {
            setStatus('error');
            return alert('Network response was not ok');
        }
        
        setStatus('success');
        return alert("Success!");
      });

  };

  return { handleSubmit, status, message };
}


export default useForm;