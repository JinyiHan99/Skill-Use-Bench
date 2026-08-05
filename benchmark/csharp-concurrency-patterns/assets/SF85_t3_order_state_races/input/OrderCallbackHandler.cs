using System.Threading.Tasks;
using eShop.Ordering.Domain.AggregatesModel.OrderAggregate;

namespace eShop.Ordering.API.Application.IntegrationEvents;

public interface IOrderRepository
{
    Task<Order> GetAsync(int orderId);
    Task UpdateAsync(Order order);
}

public class OrderCallbackHandler
{
    private readonly IOrderRepository _orderRepository;

    public OrderCallbackHandler(IOrderRepository orderRepository)
    {
        _orderRepository = orderRepository;
    }

    // These methods are invoked simultaneously by message broker callback threads (e.g., RabbitMQ, Service Bus)
    // for various callbacks (stock, payment, shipping) on any order.
    // If the same order receives stock and payment callbacks concurrently, status transitions can race or fail.
    
    public async Task HandleStockConfirmedAsync(int orderId)
    {
        var order = await _orderRepository.GetAsync(orderId);
        if (order != null)
        {
            order.SetStockConfirmedStatus();
            await _orderRepository.UpdateAsync(order);
        }
    }

    public async Task HandlePaymentPaidAsync(int orderId)
    {
        var order = await _orderRepository.GetAsync(orderId);
        if (order != null)
        {
            order.SetPaidStatus();
            await _orderRepository.UpdateAsync(order);
        }
    }

    public async Task HandleOrderShippedAsync(int orderId)
    {
        var order = await _orderRepository.GetAsync(orderId);
        if (order != null)
        {
            order.SetShippedStatus();
            await _orderRepository.UpdateAsync(order);
        }
    }
}
