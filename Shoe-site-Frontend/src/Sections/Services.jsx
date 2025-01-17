import { services } from '../Constants';
import ServiceCard from '../Components/ServiceCard';

function Services() {
  return (
    <div className="max-container flex justify-center flex-wrap gap-9">
      {services.map((service) => (
        <ServiceCard key={service.label} {...service} />
      ))}
    </div>
  );
}

export default Services;