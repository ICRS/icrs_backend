import { useState } from "react";

function useForm({ additionalData }) {
	const [status, setStatus] = useState('');

	const handleSubmit = (e) => {
		e.preventDefault();
		setStatus('loading');

		const finalFormEndpoint = e.target.action;
		const data = Array.from(e.target.elements)
			.filter((input) => input.name)
			.reduce((obj, input) => Object.assign(obj, { [input.name]: input.value }), {});

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
					return alert('User not registered. Membership may need to be acquired.');
				}

				setStatus('success');
				return alert("Success!");
			}).catch(() => {
				setStatus('error');
				return alert('Could not submit form. Please try again later.');
			});

	};

	return { handleSubmit, status };
}


export default useForm;