import React from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";

const contactSchema = z.object({
  name: z.string().min(1, "Name is required"),
  email: z.string().email("Invalid email"),
  subject: z.string().min(1, "Subject is required"),
  message: z.string().min(10, "Message must be at least 10 characters"),
});

type ContactFormData = z.infer<typeof contactSchema>;

export function ContactForm() {
  const {
    register,
    handleSubmit,
    formState: { errors },
  } = useForm<ContactFormData>({
    resolver: zodResolver(contactSchema),
  });

  const onSubmit = (data: ContactFormData) => {
    console.log("Form submitted:", data);
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)}>
      <h2>Contact Us</h2>

      <div>
        <label htmlFor="name">Name</label>
        <input id="name" {...register("name")} />
        {errors.name && <span>{errors.name.message}</span>}
      </div>

      <div>
        <label htmlFor="email">Email</label>
        <input id="email" type="email" {...register("email")} />
        {errors.email && <span>{errors.email.message}</span>}
      </div>

      <div>
        <label htmlFor="subject">Subject</label>
        <input id="subject" {...register("subject")} />
        {errors.subject && <span>{errors.subject.message}</span>}
      </div>

      <div>
        <label htmlFor="message">Message</label>
        <textarea id="message" rows={5} {...register("message")} />
        {errors.message && <span>{errors.message.message}</span>}
      </div>

      {/* TODO: Additional contact fields */}
      {/* TODO: Add file attachment support */}

      <button type="submit">Send Message</button>
    </form>
  );
}
