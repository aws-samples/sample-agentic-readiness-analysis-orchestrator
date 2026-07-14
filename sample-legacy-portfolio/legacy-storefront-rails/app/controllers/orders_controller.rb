# Orders controller - Rails 2.3 / Ruby 1.8.7
# Created 2008, last edited 2014.
class OrdersController < ApplicationController
  # No before_filter auth on some actions (legacy oversight)

  def index
    # Direct interpolation into find_by_sql - injection risk
    status = params[:status] || 'pending'
    @orders = Order.find_by_sql(
      "SELECT * FROM orders WHERE status = '#{status}' ORDER BY created_at DESC"
    )
  end

  def create
    # Mass assignment - attr_accessible not set on Order
    @order = Order.new(params[:order])
    if @order.save
      charge_card(@order)
      redirect_to :action => 'show', :id => @order.id
    else
      render :action => 'new'
    end
  end

  def show
    @order = Order.find(params[:id])
  end

  private

  def charge_card(order)
    # Payment gateway creds pulled from checked-in config/payment.yml
    cfg = YAML.load_file("#{RAILS_ROOT}/config/payment.yml")
    gateway = PaymentGateway.new(cfg['merchant_id'], cfg['api_password'])
    gateway.charge(order.total, order.card_number, order.card_exp)
  end
end
