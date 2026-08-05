import { createStateStore } from "@json-render/core";

// Initial state for the employee onboarding form
export const initialState = createStateStore({
  form: {
    firstName: "",
    confirmEmail: "",
    email: "",
    department: "",
    startDate: "",
    endDate: "",
    manager: "",
    officeLocation: "",
    needsParking: false,
    parkingLevel: "",
    emergencyContactName: "",
    emergencyContactPhone: "",
    dietaryRestrictions: "",
    agreeToTerms: false,
    notes: "",
  },
  ui: {
    currentStep: 1,
    showParkingOptions: false,
  },
});
